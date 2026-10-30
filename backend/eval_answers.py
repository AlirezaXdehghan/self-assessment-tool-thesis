import os
import pandas as pd

from auditory_evaluator import prosodic_eval
from eval_question import compare_entities, string_cleaner, remove_question_entities, cosineSim
from facial_evaluator import face_eval


def eval_answers(video_path, questions_path):
    tsv_files = []
    for filename in os.listdir(questions_path):
        if filename.endswith(".tsv"):
            name_without_extension = os.path.splitext(filename)[0]
            tsv_files.append(name_without_extension)
    
    scores = []

    for question in tsv_files:
        try:
            video = os.path.join(video_path,f"{question}_.webm")
        except:
            break
        with open(os.path.join(video_path,f"{question}_.webm.txt"),'r') as txt:
            student_answer = txt.read()
        QApair = pd.read_csv(os.path.join(questions_path,f"{question}.tsv"), index_col=0, delimiter='\t')
        row = QApair.T.iloc[0]
        QSTN = row['question']
        clean_QSTN = string_cleaner(QSTN)

        ref_ans = row['reference_answer']
        clean_ref = string_cleaner(ref_ans)
        noent_ref = remove_question_entities(clean_QSTN, clean_ref)

        good_ans = row['paraphrased']
        clean_good = string_cleaner(good_ans)
        noent_good = remove_question_entities(clean_QSTN, clean_good)

        perfect_ans = QApair.T.iloc[0]['perfect_answer']
        clean_perfect = string_cleaner(perfect_ans)
        noent_perfect = remove_question_entities(clean_QSTN, clean_perfect)

        clean_student = string_cleaner(student_answer)
        noent_student = remove_question_entities(clean_QSTN, clean_student)

        ent_score_student = max(compare_entities(noent_ref, noent_student),compare_entities(noent_good,noent_student),compare_entities(noent_perfect,noent_student))
        ent_score_good = max(compare_entities(noent_ref,noent_good), compare_entities(noent_perfect,noent_good))

        sim_score_student = max(cosineSim(noent_ref, noent_student),cosineSim(noent_good,noent_student),cosineSim(noent_perfect,noent_student))
        sim_score_good = max(cosineSim(noent_ref, noent_good),cosineSim(noent_ref,noent_perfect))

        vid_score = face_eval(video) #get facial uncertainty
        aud_score = prosodic_eval(video) #get auditory uncertainty

        if ent_score_good*0.8 <= ent_score_student:
            if sim_score_good*0.8 <= sim_score_student:
                scores.append((True, sim_score_student, ent_score_student, vid_score, aud_score))
                continue
        scores.append((False, sim_score_student, ent_score_student, vid_score, aud_score))
    return scores