import re
import pdfplumber

def extract_numbers(filename):
    # Define the regex pattern to match the first two numbers
    pattern = r'(\d+)-(\d+)'

    # Search for the pattern in the filename
    match = re.search(pattern, filename)

    if match:
        # Extract the numbers from the match groups
        num1 = int(match.group(1))
        num2 = int(match.group(2))
        return num1, num2
    else:
        return 0,-1

def find_biggest_word_portion(main_string, search_string):
    # Split the strings into lists of words
    main_words = main_string.split()
    search_words = search_string.split()
    max_length = 0
    # Iterate over all starting points in search_words
    for start in range(len(search_words)):
        for end in range(start + 1, len(search_words)//4 + 1):
            # Form the current word sequence from search_words
            current_sequence = search_words[start:end]
            current_sequence_str = " ".join(current_sequence)

            # Check if this sequence is in the main string
            if current_sequence_str in main_string:
                current_length = len(current_sequence)
                if current_length > max_length:
                    max_length = current_length

    return max_length

# Example usage

def page_from_chunk(chunkPath,pdf_path ,textSize):
    biggest_portion = 0
    with open(chunkPath, 'r') as file:
        search_string = file.read()
    start, end = extract_numbers(chunkPath)
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages[start:end]):
            main_string = ""
            for line in page.extract_text_lines():
                try:
                    if round(line['chars'][0]['size']) == textSize:
                        main_string = main_string + line['text'] + '\n'
                except:
                    continue
            biggest_portion_page = find_biggest_word_portion(main_string, search_string)
            if biggest_portion_page > biggest_portion:
                biggest_portion = biggest_portion_page
                max_page = index
    return {'starting_page':max_page + start + 1}