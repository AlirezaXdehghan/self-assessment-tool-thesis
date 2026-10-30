# Self Assessment Tool for Medical Exam Candidates

**MSc thesis** — University of Padova, Department of Mathematics, Academic Year 2023/24
Candidate **Alireza Dehghan** · Supervisor **Prof. Massimo Marchiori** · Co-supervisor **Davide Baldelli**

📄 **[The thesis](docs/thesis/dehghan-2024-self-assessment-tool.pdf)**

An automated oral examination for medical students. It reads a textbook, writes exam questions from it, records the candidate answering them aloud, and scores each answer on three axes — content, prosody, facial expression — approaching the way a human examiner reads both knowledge and confidence.

The tool has two main components: the natural language processing and the multimodal analysis components. The NLP component is responsible for question generation from provided textbooks, speech-to-text for oral responses, and further evaluation of such responses. This is achieved through the use of advanced language models (LLMs) in ensuring parsing and generation of accurate medical-related content. This evaluation is enriched with multimodal analysis that will treat prosodic features and facial expressions to identify student confidence and uncertainty to resemble an evaluation as of human examiners.


## How a session runs

| # | Step | Code |
|---|------|------|
| 1 | A textbook PDF is uploaded, digested into sections, located by page and cut into overlapping chunks | `backend/digest.py`, `backend/findPage.py`, `POST /uploadPDF` |
| 2 | Questions are generated from the material, each with a reference answer, a paraphrase and a perfect answer | `backend/generate_QApair.py`, `backend/model_pipeline.py`, `POST /createtheexam/{uuid}` |
| 3 | The candidate sits the exam in the browser; each answer is recorded from the webcam | `frontend/src/components/exam.js`, `ExamCreator.js` |
| 4 | Answers are transcribed with Whisper and scored against the expected answers, by sentence embeddings and entity overlap | `backend/eval_answers.py`, `backend/eval_question.py` |
| 5 | Prosody and facial expression add uncertainty signals | `backend/auditory_evaluator.py`, `backend/facial_evaluator.py` |
| 6 | Results are served, and optionally emailed to the candidate | `GET /EvaluateExam/{uuid}`, `backend/emailScore.py` |

## Layout

| Path | What |
|------|------|
| `frontend/` | React — CRA, Redux, `react-webcam` |
| `backend/` | FastAPI service — ingestion, generation, transcription, scoring |
| `experiments/` | Answer-scoring notebook, used while developing the evaluation |
| `docs/thesis/` | The thesis |

The trained assets travel with the backend: `bestmo2.keras` (facial expression) and `scaler-prosody.joblib` (prosody calibration).

## Running it

**Backend** — Python, with the versions in `req.txt`. A CUDA GPU is effectively required: Whisper, `sentence-transformers` and the quantised LLMs all assume one.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate elsewhere
pip install -r req.txt
```

Then set the environment variables from `backend/.env.example` and start it:

```bash
uvicorn app:app --port 8000
```

Uploads, transcripts and the Whisper download go to `backend/WorkDir`, unless `WORK_DIRECTORY` points somewhere else. Hugging Face weights go to `HF_HOME`, defaulting to `~/.cache/huggingface`. `CUDA_VISIBLE_DEVICES` selects the GPU and defaults to `0`.

**Frontend:**

```bash
cd frontend
npm install
npm start
```

The app reads its backend address from `REACT_APP_BACKEND_URL`; without it, it falls back to the original deployment address:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000 npm start
```

## Credentials

None are in this repository. Three values are needed at runtime, all read from the environment:

| Variable | Used for |
|---|---|
| `PROTON_USER`, `PROTON_PASSWORD` | The mailbox that emails results to candidates |
| `HF_TOKEN` | Hugging Face access token for the gated checkpoints |

They were stripped on import from `SA-Back`, where they had been committed in plaintext. **Treat all three as compromised and rotate them** — removing them here does not remove them from that repository's history.
