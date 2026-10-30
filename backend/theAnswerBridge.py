from video_parsing import speech2text
from emailScore import sendScore
from eval_answers import eval_answers
import os
WORK_DIRECTORY = "/home/looporchestra/Projects/Self-Assessment-Tool/WorkDir"



def response2results(file_path: str, directory: str, timestamps, model, uuid, emailRecipient):
    video_path = os.path.join(os.path.join(WORK_DIRECTORY, uuid), 'video/')
    question_path = os.path.join(os.path.join(WORK_DIRECTORY, uuid), 'questions/')

    speech2text(file_path, directory, timestamps, model) #cut videos, convert speech to text

    results = eval_answers(video_path, question_path) #get the result of facial, prosodic and textual eval

    sendScore(results, emailRecipient, uuid) #send the results to the user