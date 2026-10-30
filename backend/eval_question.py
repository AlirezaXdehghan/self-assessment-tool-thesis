import string
import re
import pandas as pd
import spacy
import inflect
from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.stats import spearmanr
from nltk.stem import PorterStemmer
import textdistance
import torch
import csv

stemmer = PorterStemmer()
p = inflect.engine()
nlp = spacy.load("en_core_sci_lg")
#model = SentenceTransformer("all-MiniLM-L6-v2")
#model = SentenceTransformer("all-distilroberta-v1")
model = SentenceTransformer("all-mpnet-base-v2")

def replace_separators_with_space(input_string):
    separators = ["-", "_", ".", ",", ";", ":", "/", "\\", "|", "!", "?", "'"]
    for separator in separators:
        input_string = input_string.replace(separator, " ")
    return input_string

def remove_question_entities(question, answer):
    Q_processed = nlp(question)
    ANS_processed = nlp(answer)
    Q_entities = set([word for ent in list(Q_processed.ents) for word in ent.text.split()])
    Q_abbs = set([create_abbreviation(ent.text) for ent in Q_processed.ents])
    #ANS_entities = set([word for ent in list(ANS_processed.ents) for word in ent.text.split()])
    #ANS_toremove = ANS_entities.intersection(Q_entities) #meh is it really needed tho?
    ANS_to_remove = Q_entities.union(Q_abbs)
    clean_ans = answer_cleaner(answer, ANS_to_remove)
    return clean_ans

def answer_cleaner(orig, setRem):
    orig = orig.lower()
    for wrd in setRem:
        orig = orig.replace(wrd,'')
    return orig

def string_cleaner(sentence):
    punctuations = string.punctuation
    stop_words = nlp.Defaults.stop_words
    sentence = re.sub(r'\d+', r' \g<0> ', sentence)
    sentence = replace_separators_with_space(sentence)
    tokens = nlp(sentence)
    tokens = [word.lemma_.lower().strip() for word in tokens]
    tokens = [word for word in tokens if (word not in stop_words and word not in punctuations) or word.isdigit()]
    tokens = [word if not word.isdigit() else p.number_to_words(word) for word in tokens]
    sentence = ' '.join(tokens)
    sentence = sentence.replace('<',' less than ')
    sentence = sentence.replace('>',' more than ')
    sentence = sentence.replace('≥',' greater than or equal to ')
    sentence = sentence.replace('≤',' less than or equal to ')
    sentence = sentence.replace('=',' equal to ')
    return sentence

def load_abbreviations(filename):
    abbrev_to_full = {}
    full_to_abbrev = {}

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            abbreviation = row[0].strip()
            full_texts = [text.strip() for text in row[1].split('/')]
            abbrev_to_full[abbreviation] = full_texts
            for full_text in full_texts:
                if full_text not in full_to_abbrev:
                    full_to_abbrev[full_text] = []
                full_to_abbrev[full_text].append(abbreviation)

    return abbrev_to_full, full_to_abbrev

def cosineSim(reference, answer):
    """
    :param reference:
    :param answer:
    :return:
    cosine similarity between the BERT encoded strings
    """
    REFANS_embedding = model.encode(reference)
    STDANS_embedding = model.encode(answer)
    return util.cos_sim(REFANS_embedding, STDANS_embedding).item()

def ro_matcher(word1,word2, threshold=0.90):
    if textdistance.ratcliff_obershelp.normalized_similarity(word1,word2) >= threshold:
        return True
    else:
        return False

def partial_intersection(set1, set2, threshold):
    intersection = set()
    for word1 in set1:
        for word2 in set2:
            if ro_matcher(word1, word2, threshold):
                intersection.add(word1)
                break  # If we find a match, we can stop checking the current word1
    return intersection

def sort_by_gap(t):
    squaredError1 = (100 - t[1]*100)**2 + (t[2]*100)**2
    return squaredError1

def create_abbreviation(word):
    common_words = ["and", "of", "the", "in", "on", "at", "for", "to", "with", "by", "from"]
    # Split the word into individual words
    dc = nlp(word)
    core_words = []
    for token in dc:
        if not token.is_punct:
            core_words.append(token.text)
    if len(core_words) <=1:
        return 'NaN'
    # Get the first letter of each significant word and concatenate them
    abbreviation = ''.join(word[0] for word in core_words if word.lower() not in common_words).lower()
    return abbreviation

def add_abbreviation(input_list):
    result = set(input_list)
    abb_full, full_abb = load_abbreviations('abbs.csv')
    for item in input_list:
        if item in abb_full:
            result.update(abb_full[item])
        if item in full_abb:
            result.update(full_abb[item])
        else:
            for full in full_abb.keys():
                if ro_matcher(item,full):
                    result.update(full_abb[full])
    return list(result)

def compare_entities(reference, std_answer, threshold = 0.90):
    """
    :param reference:
    :param std_answer:
    :return:
    splitted lemma matching
    """
    ref_processed = nlp(reference)
    std_processed = nlp(std_answer)
    abb_from_ents = [create_abbreviation(ent.text) for ent in std_processed.ents if create_abbreviation(ent.text) != 'NaN']
    abb_from_file = add_abbreviation([ent for ent in std_processed.ents])
    ref_ents = [stemmer.stem(token) for ent in ref_processed.ents for token in ent.text.lower().split()]
    std_ents = [stemmer.stem(token) for ent in std_processed.ents for token in ent.text.lower().split()]
    ref_NUM = [token.text for token in ref_processed if token.pos_ == "NUM"]
    std_NUM = [token.text for token in std_processed if token.pos_ == "NUM"]
    ref_keywords = set(ref_ents + ref_NUM)
    std_keywords = set(std_ents + std_NUM)
    allstd = std_keywords.union(set(abb_from_ents)).union(set(abb_from_file))
    intersection = partial_intersection(ref_keywords,allstd, threshold) #number of tokens that are in both answers
    #intersection = ref_keywords.intersection(allstd)
    if len(ref_keywords) == 0 or len(std_keywords) == 0 or len(intersection) ==0:
        return 0
    precision = (len(intersection)/len(std_keywords))
    recall = len(intersection)/len(ref_keywords)
    return (2*precision*recall) / (precision + recall)
    #return str(len(intersection)/len(ref_keywords))

def compare_bm25_binary(reference_ranking, std_answer_ranking, precentile=80):
    """
    :param reference_ranking:
    :param std_answer_ranking:
    :param precentile:
    :return:
    Matching indexes precentage
    """
    ref_precentile = np.percentile(reference_ranking,precentile)
    std_precentile = np.percentile(std_answer_ranking, precentile)
    reference_ranking = [1 if x >= ref_precentile else 0 for x in reference_ranking]
    std_answer_ranking =  [1 if x >= std_precentile else 0 for x in std_answer_ranking]
    binary_score_list = [1 if a == b == 1 else 0 for a, b in zip(reference_ranking, std_answer_ranking)]
    binary_score = sum(binary_score_list)/sum(reference_ranking)
    return str(binary_score)

def compare_bm25(reference_ranking, std_answer_ranking, precentile=80):
    """
    :param reference_ranking:
    :param std_answer_ranking:
    :param precentile:
    :return:
    Spearman Coefficient
    """
    ref_precentile = np.percentile(reference_ranking,precentile)
    std_precentile = np.percentile(std_answer_ranking, precentile)
    reference_ranking = [x if x >= ref_precentile else 0 for x in reference_ranking]
    std_answer_ranking =  [x if x >= std_precentile else 0 for x in std_answer_ranking]
    spearman_corr , p_value = spearmanr(reference_ranking,std_answer_ranking)
    return str(spearman_corr)

def semantic_search(corpus, queries):
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    top_k = min(5, len(corpus))
    for query in queries:
        query_embedding = model.encode(query, convert_to_tensor=True)

    # We use cosine-similarity and torch.topk to find the highest 5 scores
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = torch.topk(cos_scores, k=top_k)

    print("\n\n======================\n\n")
    print("Query:", query)
    print("\nTop 5 most similar sentences in corpus:")

    for score, idx in zip(top_results[0], top_results[1]):
        print(corpus[idx], "(Score: {:.4f})".format(score))