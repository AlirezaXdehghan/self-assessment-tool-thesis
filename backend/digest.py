import os
import re
import pdfplumber
import uuid
from collections import Counter
import logging
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os


def analyze_fonts_and_sizes(pdf):
    font_counter = Counter()
    size_counter = Counter()
    for page in pdf:
        for text in page.extract_text_lines():
            if text['text']:
                font = text['chars'][0]['fontname']
                size = round(text['chars'][0]['size'])
                font_counter[font] += 1
                size_counter[size] += 1

    fonts = font_counter
    sizes = size_counter
    return fonts, sizes


def checkRegEx(size, file):
    patternDotChapter = r'\d+\.\s.*$'
    patternFindChapter = r'.*chapter.*'
    for index, page in enumerate(file.pages):
        for text in page.extract_text_lines():
            if text['text']:
                if round(text['chars'][0]['size']) == size:
                    if re.findall(patternFindChapter, text['text'], flags=re.IGNORECASE) or re.findall(
                            patternDotChapter, text['text'], flags=re.IGNORECASE):
                        logging.info("Matched RegEx", text['text'])
                        return True
    return False


def checkStatistics(lastPage, section):

    q1 = np.percentile(section, 25)
    q3 = np.percentile(section, 75)
    std = round(np.std(section), 1)
    #(size, "#sections =", len(section), "| var = ", round(np.var(section), 1), "| std ", std,
    #      "| coverage per section = ", round(100 * (q3 - q1 + np.mean(section)) / lastPage, 1), "| interQ = ", q3 - q1)
    return np.var(section), std, round(100 * (q3 - q1 + np.mean(section)) / lastPage, 1), q3 - q1


def create_size_dictionary(file, most_common_sizes,textSize):
    z = dict()
    for size in most_common_sizes:
        if most_common_sizes[size] > 50:
            continue
        if size <= textSize:
            continue
        x = []
        for index, page in enumerate(file.pages):
            for text in page.extract_text_lines():
                if text['text']:
                    if round(text['chars'][0]['size']) == size:
                        x.append(index)
        x = sorted(list(set(x)))
        if len(x) > 1:
            z[size] = x
    return z


def create_size_section_dictionary(size_dic,lastPage):
    sections = dict()
    for size in size_dic.keys():
        startPage = 0
        coveragePages = []
        for cutPage in size_dic[size]:
            coveragePages.append(cutPage - startPage)
            startPage = cutPage
        coveragePages.append(lastPage - startPage)
        sections[size] = coveragePages[1:-1]
    return sections


def find_seperator_size(sections,file,lastPage):
    validRegEx = []
    for size in sections.keys():
        if checkRegEx(size, file):
            validRegEx.append(size)

    if validRegEx:
        chapterSize = max(validRegEx)

    elif len(sections.keys()) == 1:
        chapterSize = sections.keys()[0]

    else:
        goodSizes = []
        coverageLimit = 20
        sectionLimit = 7
        while not goodSizes and coverageLimit <= 40:
            for size in sections.keys():
                section = sections[size]
                variance, std, coverage, interQ = checkStatistics(lastPage, section)
                if not (len(section) < sectionLimit or variance < 1 or coverage > coverageLimit or interQ < 1):
                    goodSizes.append(size)
            if goodSizes:
                chapterSize = max(goodSizes)
            coverageLimit += 5
    return chapterSize

def is_majority_element(counter):
    if len(counter) == 0:
        return False

    most_common, most_common_count = counter.most_common(1)[0]
    total_count = sum(counter.values())

    return most_common_count > total_count * 0.5

def cut_pdf(pagesToCut, inputPDF):
    PDFs = []
    startPage = 0
    for index, cut in enumerate(pagesToCut):
        if startPage == cut:
            continue
        pdf_section = inputPDF.pages[startPage: cut]
        startPage = cut
        PDFs.append(pdf_section)
    PDFs.append(inputPDF.pages[startPage:])
    return PDFs

def clean_pdfs(pdfs, most_common_fonts):
    toDelete = []
    for part in pdfs:
        common_font, common_size = analyze_fonts_and_sizes(part)
        try:
            if not (common_font.most_common(1)[0][0] == most_common_fonts.most_common(1)[0][0] and is_majority_element(
                    common_size)):
                toDelete.append(part)
        except:
            toDelete.append(part)

    final_list = [x for x in pdfs if x not in toDelete]
    return final_list

def write_texts(sectionList, outputFolder,textSize,lastPage):
    try:
        os.makedirs(outputFolder,exist_ok=True)
    except:
        logging.exception("Folder Already Exists or bad directory")
    PagesList = []
    for index, section in enumerate(sectionList):
        firstPage = sum(len(sec) for sec in sectionList[0:index])
        lastPage = firstPage + len(section)
        PagesList.append((firstPage,lastPage))
        filename = outputFolder + str(index) + '.txt'
        with open(filename, 'w') as txt:
            for page in section:
                for line in page.extract_text_lines():
                    try:
                        if round(line['chars'][0]['size']) == textSize:
                            txt.write(line['text'] + '\n')
                    except:
                        continue
    return PagesList



def calculate_similarity(text1, text2):
    # Preprocess the texts
    preprocessed_texts = [text1, text2]

    # Calculate TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(preprocessed_texts)

    # Compute cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

    return similarity
def findStartEnd(txt_files, folder):

    all= []
    for index1 in range(int(len(txt_files)/1.3)):
        com = []
        file1 = folder + str(index1)+'.txt'
        with open(file1,'r') as file:
            text1 = file.read()
        for index2 in range(int(len(txt_files)/1.3)):
            file2 = folder + str(index2)+'.txt'
            if index1 >= index2:
                continue
            with open(file2, 'r') as file:
                text2 = file.read()
            com.append(calculate_similarity(text1,text2))
        if com:
            all.append(com)
    s = []
    for a in all:
        s.append(np.mean(a))

    for index in range(len(s)):
        if np.mean(s)*0.9 < s[index]:
            start = index
            break

    all= []
    for index1 in range(start, len(txt_files)):
        com = []
        file1 = folder+ str(index1)+'.txt'
        with open(file1,'r') as file:
            text1 = file.read()
        for index2 in range(start,len(txt_files)):
            file2 = folder+ str(index2)+'.txt'
            if index1 <= index2:
                continue
            with open(file2, 'r') as file:
                text2 = file.read()
            com.append(calculate_similarity(text1,text2))
        if com:
            all.append(com)
    s = []
    for a in all:
        s.append(np.mean(a))
    for index in reversed(range(len(s))):
        if np.mean(s)*0.9 < s[index]:
            end = index + (len(txt_files)-len(s))
            break
    return start,end+1

def create_text_chunks(folder, pages , starting_file, ending_file, chunk_length, chunk_overlap):
    chunk_folder = os.path.join(folder,'chunks/')
    try:
        os.mkdir(chunk_folder)
    except FileExistsError:
        logging.exception("Folder Already Exists")
        pass
    for index in range(starting_file,ending_file):
        file_path = os.path.join(os.path.join(folder, 'sections/'), str(index)+'.txt')
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        tokens = text.split() #nltk who?
        chunks = []
        start_index = 0

        while start_index < len(tokens)-chunk_overlap:
            end_index = min(start_index + chunk_length, len(tokens))
            chunks.append(' '.join(tokens[start_index:end_index]))
            start_index = start_index + (chunk_length - chunk_overlap)

        for i, chunk in enumerate(chunks):
            filename = f"{chunk_folder}/{pages[index][0]}-{pages[index][1]}_chunk_{i}_{index}.txt"
            with open(filename, 'w', encoding='utf-8') as chunk_file:
                chunk_file.write(chunk)

def start_digesting(input, newFolder):
    start = time.time()
    print("Starting!")
    file = pdfplumber.open(os.path.join(input,'raw.pdf'))
    lastPage = len(file.pages) - 1
    most_common_fonts, most_common_sizes = analyze_fonts_and_sizes(file.pages)
    textSize = most_common_sizes.most_common(1)[0][0]
    size_dic = create_size_dictionary(file, most_common_sizes,textSize)
    sections = create_size_section_dictionary(size_dic,lastPage)
    chapterSize = find_seperator_size(sections,file,lastPage)
    pdfs = cut_pdf(size_dic[chapterSize], file)
    clean = clean_pdfs(pdfs, most_common_fonts)
    output_folder = os.path.join(input,'sections/')
    pagenums = write_texts(clean, output_folder,textSize,lastPage)
    print("happily Chunked!")
    txt_files = [file for file in os.listdir(output_folder) if file.endswith('.txt')]
    strt, end = findStartEnd(txt_files, output_folder)
    create_text_chunks(input, pagenums, starting_file=0, ending_file=len(pdfs)-1, chunk_length=1500, chunk_overlap=250)
    print("happily wrote chunks to disks!")
    endt = time.time()
    print("total time:", endt - start)
    return {'uuid': newFolder,
            'starting_chapter':strt,
            'last_chapter':end,
            'number_chapters': len(pdfs)-1,
            'textSize':textSize,
            'time':endt-start}
