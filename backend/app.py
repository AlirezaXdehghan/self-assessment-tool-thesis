import json
import shutil

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os

from theAnswerBridge import response2results

os.environ['HF_HOME'] = os.environ.get('HF_HOME', os.path.join(os.path.expanduser('~'), '.cache', 'huggingface'))
os.environ['TRANSFORMERS_CACHE'] = os.environ['HF_HOME']
# HF_TOKEN comes from the environment; never committed. See .env.example

import uuid
import whisper
from typing import Dict, Tuple, Annotated, List
from pydantic import BaseModel, Field
from digest import start_digesting
from generate_QApair import genQA
from findPage import page_from_chunk
from model_pipeline import LLMModel
from theAnswerBridge import response2results
from eval_answers import eval_answers
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

model_dir = "/home/looporchestra/Projects/Talking_Face/MR_Code/code/lama/Meta-Llama-3-8B-Instruct"
llm = LLMModel(llm_checkpoint='meta-llama/Meta-Llama-3-8B-Instruct')
app = FastAPI()
origins = [
    "http://selfassess.vercel.app",
    "https://selfassess.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
WORK_DIRECTORY = os.environ.get("WORK_DIRECTORY", os.path.join(os.path.dirname(os.path.abspath(__file__)), "WorkDir"))
if not os.path.exists(WORK_DIRECTORY):
    os.makedirs(WORK_DIRECTORY)
model = whisper.load_model("tiny.en", download_root=WORK_DIRECTORY)
class Times(BaseModel):
    data: Dict[Annotated[int, Field(strict=False)], Tuple[float, float]]


class Timestamps(BaseModel):
    timestamps: List[int]


@app.post('/uploadPDF')
async def process_pdf(uploaded_file: UploadFile = File(...)):
    try:
        newFolder = str(uuid.uuid4()).replace("-", "")
        instanceDir = os.path.join(WORK_DIRECTORY, newFolder)
        if not os.path.exists(instanceDir):
            os.makedirs(instanceDir)
        file_location = os.path.join(instanceDir, f"raw.pdf")
        with open(file_location, "w+b") as file:
            shutil.copyfileobj(uploaded_file.file, file)
        return start_digesting(instanceDir, newFolder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/findPage/{text_size}/{uuidN}/{id}")
async def find_page(id: str, uuidN: str, text_size: int):
    # using id get chunkpath and pdf path and textsize
    chunk_path = os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'chunks/')
    input_file = os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'raw.pdf')
    return page_from_chunk(chunk_path, input_file, text_size)


@app.get('/showSection/{uuidN}/{section}')
async def get_text(section: int, uuidN: str):
    text_path = os.path.join(os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'sections/'), f"{section}.txt")
    with open(text_path, 'r') as file:
        text = file.read()
    return {"text": text}


@app.post('/createtheexam/{uuidN}')
async def createexam(uuidN: str, validSections: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    print("generating questions!")
    valid_sections = json.loads(validSections)
    directory = os.path.join(WORK_DIRECTORY, uuidN)
    background_tasks.add_task(genQA, valid_sections, directory, llm)
    return{'status': 'success'}


@app.get('/showquestion/{uuidN}/{qnum}')
async def get_question(qnum: int, uuidN: str):
    # if somehow we have the upload path
    question_path = os.path.join(os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'questions/'), f"{qnum}.tsv")
    try:
        question_csv = pd.read_csv(question_path, index_col=0, delimiter='\t')
        question = question_csv.T.iloc[0]['question']
    except:
        return{"question": "Congrats! you can finish now"}
    return {"question": question}


@app.post('/processVideo/{uuidN}')
async def process_video(uuidN: str, video: UploadFile = Form(...), timestamps: str = Form(...), email: str = Form(...),
                        background_tasks: BackgroundTasks = BackgroundTasks()):
    video_path = os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'video/')
    if not os.path.exists(video_path):
        os.makedirs(video_path)
    file_path = os.path.join(video_path, 'answer.webm')
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    timestamps_data = json.loads(timestamps)
    background_tasks.add_task(response2results, file_path, video_path, timestamps_data, model, uuidN, email)
    print({"filename": video.filename, "timestamps": timestamps_data})
    return {"filename": video.filename, "timestamps": timestamps_data}

@app.get('/EvaluateExam/{uuidN}')
async def evaluate_exam(uuidN: str):
    video_path = os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'video/')
    question_path = os.path.join(os.path.join(WORK_DIRECTORY, uuidN), 'questions/')
    scores = eval_answers(video_path,question_path)
    print("the scores are:",scores)
    return({"scores": scores})
