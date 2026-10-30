# Self Assessment Tool for Medical Exam Candidates

**MSc thesis** — University of Padova, Department of Mathematics, Academic Year 2023/24
Candidate **Alireza Dehghan** · Supervisor **Prof. Massimo Marchiori** · Co-supervisor **Davide Baldelli** (LoopAI)

📄 **[Read the thesis (61 pages)](docs/thesis/dehghan-2024-self-assessment-tool.pdf)**

---

## What it is

An automated oral examination for medical students. It reads a textbook, writes exam questions from it, records the candidate answering them aloud, and scores each answer on three axes — content, prosody, facial expression — approaching the way a human examiner reads both knowledge and confidence.

> The tool has two main components: the natural language processing and the multimodal analysis components. The NLP component is responsible for question generation from provided textbooks, speech-to-text for oral responses, and further evaluation of such responses. This is achieved through the use of advanced language models (LLMs) in ensuring parsing and generation of accurate medical-related content. This evaluation is enriched with multimodal analysis that will treat prosodic features and facial expressions to identify student confidence and uncertainty to resemble an evaluation as of human examiners.
>
> — Abstract

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

| Path | What | Where it came from |
|------|------|--------------------|
| `frontend/` | React 18 app — CRA, Redux, `react-webcam` | This repository's own history, formerly `SATUI` |
| `backend/` | FastAPI service — ingestion, generation, transcription, scoring | Snapshot of `SA-Back` @ `15f5606` |
| `experiments/` | Answer-scoring notebook, used while developing the evaluation | Snapshot of `sentence-evaluation` @ `c366a94` |
| `docs/thesis/` | The thesis | — |

The trained assets travel with the backend: `bestmo2.keras` (facial expression) and `scaler-prosody.joblib` (prosody calibration).

`package.json` also declares `face-api.js` and `react-pdf`, neither of which is imported anywhere. Facial analysis runs on the backend (`facial_evaluator.py`), and the browser never renders the PDF: `GET /showSection/{uuid}/{n}` returns the extracted section text, which the app simply displays. Both packages are left in place because the lockfile was generated with them.

**Two relatives are deliberately not merged.** `backself` is the predecessor of `SA-Back` — `abbs.csv` and `findPage.py` are byte-identical, the rest was superseded — so importing it would add nothing but a second copy. `PDFdigester` is a standalone tool used well beyond this thesis and continues on its own; the version this work used is pinned at `1247dcf`.

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

## Known defects, kept on purpose

This is an archived thesis: the code is preserved as it was run, not repaired. Two things are worth knowing before reading any number it produces.

- **`backend/eval_answers.py:49`** — `cosineSim(noent_perfect, noent_perfect)` compares the perfect answer with itself, so `sim_score_good` is always `1.0`. The `0.8` threshold on the next line therefore means "the candidate reached 0.8 cosine similarity", not "80% of a good answer". The intended expression is `cosineSim(noent_ref, noent_perfect)`.
- **No automated tests.** The system was validated by using it, plus the experiments in `experiments/`.

## Changes made on import

Only what was needed to make the code runnable and safe, listed so the record stays honest:

- Three credentials replaced with environment lookups (`app.py`, `emailScore.py`, `generate_openelm.py`, `model_pipeline.py`).
- The hardcoded home directory in `app.py` and the hardcoded GPU index replaced with environment defaults.
- The frontend's hardcoded backend address made overridable via `REACT_APP_BACKEND_URL`.
- `.DS_Store` and `.idea/` not carried over.
