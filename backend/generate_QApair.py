import torch
import os
from eval_question import string_cleaner, remove_question_entities, cosineSim, sort_by_gap
import pandas as pd
WORK_DIRECTORY = "/home/looporchestra/Projects/Self-Assessment-Tool/WorkDir"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
print('Number CUDA Devices:', torch.cuda.device_count())
model_dir = "/home/looporchestra/Projects/Talking-Face/MR_Code/code/lama/Meta-Llama-3-8B-Instruct"
output = pd.DataFrame()
device = 'cuda'


def getBestQA(QAs,llm):
    """
    :param QAs: a list of questions
    :return: string of Question, answer and other things to be parsed!

    take into account if all the list failed as questions, then what?
    """
    noent_wrong_list_similarities,noent_good_list_similarities=[],[]
    for index, row in QAs.iterrows():
        QSTN = row['question']
        clean_QSTN = string_cleaner(QSTN)
        ref_ans = row['reference_answer']
        clean_ref = string_cleaner(ref_ans)
        noent_ref = remove_question_entities(clean_QSTN, clean_ref)
        good_ans = row['paraphrased']
        clean_good = string_cleaner(good_ans)
        noent_good = remove_question_entities(clean_QSTN, clean_good)
        wrong_ans = row['wrong_answer']
        clean_wrong = string_cleaner(wrong_ans)
        noent_wrong = remove_question_entities(clean_QSTN, clean_wrong)
        noent_good_list_similarities.append(cosineSim(noent_ref,noent_good))
        noent_wrong_list_similarities.append(cosineSim(noent_ref, noent_wrong))
    test = []
    for index, x in enumerate(zip(noent_good_list_similarities, noent_wrong_list_similarities)):
        z = x[1]
        x = x[0]
        test.append((index, float(x), float(z)))

    sorted_data = sorted(test, key=sort_by_gap, reverse=False)
    best_questions = [QAs.iloc[item[0]] for item in sorted_data if sort_by_gap(item) < 5000]
    if not best_questions:
        best_questions = [QAs.iloc[sorted_data[0][0]]]
    return best_questions


def genQA(valid_sections, directory, llm):
    #dir = uuid/
    chunks_dir = os.path.join(directory, 'chunks/')
    QA_dir = os.path.join(directory, 'questions/')
    if not os.path.exists(QA_dir):
        os.makedirs(QA_dir)
    Qnumber = 0
    for section in valid_sections:
        QAs = []
        #let's say I get the chunk path somehow (os list ending with index.txt)
        suffix = f'_{section}.txt'
        matching_files = [f for f in os.listdir(chunks_dir) if f.endswith(suffix)]
        if Qnumber >= 10:
            break
        for chunk in matching_files:
            file = os.path.join(chunks_dir, chunk)
            QAgood, newQA = chunk2QA(file, llm)
            if QAgood:
                QAs.append(newQA) #generate for each chunk
        if len(QAs) != 0:
            print(f"A new question has been generated! {Qnumber}")
            bestQA = getBestQA(pd.concat(QAs, ignore_index=True), llm) #best question out of all chunks!
            for qa in bestQA:
                qa.to_csv(os.path.join(os.path.join(QA_dir, f"{Qnumber}.tsv")), sep='\t')
                Qnumber += 1


def chunk2QA(chunk_path, llm):
    output = pd.DataFrame()
    with open(os.path.join(WORK_DIRECTORY,'prompt_all_llama.txt'),'r') as file:
        prompt_template = file.read()
    with open(chunk_path,'r') as file:
        chunk_text = file.read()
    if len(chunk_text.split(" ")) < 250:
        return False, output
    prompt = prompt_template.replace('{toreplacebychunk}', chunk_text)
    llama_prompt = [
   {"role": "system", "content": "Avoid saying 'According to the text' and similiar references. Do not generate anything more than what is asked. this is for scientific purposes and you shouldn't use previous knowledge"},
    {"role": "user", "content": prompt}]
    decoded = llm.lama_inference(prompt=llama_prompt)
    print(decoded)
    if 'no question' in decoded.split('assistant')[1].lower():
        return False, output
    try:
        question = decoded.split('GenQues:')[1].split('GenAns:')[0]
        ref_answer = decoded.split('GenAns:')[1].split('PrfctAns:')[0]
        perfect_answer = decoded.split('PrfctAns:')[1].split('GdAns:')[0]
        paraphrased_answer = decoded.split('GdAns')[1].split('IncorrectAnswer:')[0]
        wrong_answer = decoded.split('IncorrectAnswer:')[1]
        output = output._append({'chunk': chunk_path,'question':question, 'reference_answer':ref_answer, 'perfect_answer': perfect_answer, 'paraphrased': paraphrased_answer, 'wrong_answer': wrong_answer}, ignore_index=True)
    except:
        return False, output
    return True, output