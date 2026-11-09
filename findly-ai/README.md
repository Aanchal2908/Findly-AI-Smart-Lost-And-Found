# Findly AI

A responsive Streamlit app for a university campus lost-and-found matching capstone. Reports and claim workflow updates live only in the active Streamlit session. AI Matches keeps the TF-IDF lexical ranker as its default baseline and offers an optional pretrained MiniLM sentence-embedding mode.

## Project files

- `app.py` contains the Streamlit interface, sample reports, navigation, filters, reporting form, match review, item details, and session-only claim flow.
- `match_engine.py` computes TF-IDF cosine text similarity and combines it with category, location-token, and date relevance.
- `semantic_matcher.py` lazily loads the pretrained `sentence-transformers/all-MiniLM-L6-v2` model from the local cache only; it never downloads a model automatically and falls back to the lexical ranker when unavailable.
- `evaluation.py` contains a fixed, hand-labeled pairwise dataset and computes metrics through the production ranker and threshold. It does not read session-state reports.
- `requirements-semantic.txt` lists the optional embedding dependency; it is not part of the default installation.
- `test_match_engine.py`, `test_semantic_matcher.py`, and `test_evaluation.py` cover baseline behavior, optional fallback, metric formulas, and evaluation scenarios.
- `requirements.txt` lists the single runtime dependency.

## Windows setup

From PowerShell, open the project directory:

```powershell
cd E:\lostandfound\findly-ai
```

Create and activate a virtual environment if you do not already have one:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies and run the app:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

Run all matching and evaluation tests from the workspace root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\findly-ai -p "test_*.py" -v
```

## Optional Semantic Setup

MiniLM is a pretrained general-purpose sentence encoder, not a model trained by this project. The model has 384-dimensional embeddings and roughly 90 MB of weights. Installing `sentence-transformers` also installs its PyTorch/Transformers runtime; package size varies by Python/platform and can be substantially larger than the model weights. The app stays on TF-IDF unless the optional mode is selected.

After approving setup, run these commands from `E:\lostandfound` to install the optional package and download/cache the model once:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\findly-ai\requirements-semantic.txt
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')"
```

The first command needs package-index access. The second needs network access and downloads model files (about 90 MB) into the Hugging Face cache. Afterwards the app uses `local_files_only=True`; semantic mode will not fetch updates and will fall back to TF-IDF if files are missing. The existing environment is Python 3.14.7; semantic package installation and PyTorch wheel compatibility have not been tested for this interpreter. If no compatible wheel is available, use a Python version supported by the selected PyTorch/Sentence-Transformers releases.

If you prefer to reuse the workspace virtual environment that already exists one directory above this project, run these commands from `E:\lostandfound` instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\findly-ai\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run .\findly-ai\app.py
```

## Demo scope

- Browse filters, form validation, session-created reports, and claim status controls work locally.
- Match scores rank text/context similarity and are not probabilities that an item belongs to someone. TF-IDF cannot recognize synonyms without word overlap. MiniLM may recognize paraphrases, but can still miss synonyms or produce false positives.
- Only Lost reports are compared with Found reports. Candidates below the minimum text and score thresholds are omitted.
- The Evaluation page compares both modes over the same four fixed Lost/Found pairs: exact wording, partial overlap, unrelated items, and synonym-only wording. The verified TF-IDF baseline results are TP=2, FP=0, TN=1, FN=1; precision=100.0%, recall=66.7%, and F1=80.0%. Metrics return 0 when their denominator is zero. MiniLM results are not measured until its optional package and model are installed and cached.
- These metrics describe only a small hand-labeled demonstration dataset and do not establish general real-world accuracy or semantic understanding. The baseline's synonym miss is observed; MiniLM's outcome on that example must be measured after setup.
- No database, authentication, notifications, email, or real messaging is connected.
- Sample item photos and the Plus Jakarta Sans / Material Symbols fonts load from Unsplash and Google Fonts, so those assets require an internet connection. The interface and controls remain usable without them.
