# TPRM Chatbot

A small RAG application that answers third-party risk questionnaires using only the
documents uploaded with them. A Claude model on Azure AI Foundry does the answering;
retrieval keeps it grounded in the uploaded files.

## Files
- `rag.py` - the engine: settings, PDF chunking, FAISS index, retrieval, and the
  RAG and baseline calls to the model. Run directly to index the compiled PDFs.
  Auth uses the `AZURE_KEY` environment variable if set, otherwise `az login`.
- `app.py` - Streamlit UI: upload source documents and a questionnaire and answer
  each question with a source citation.
- `evaluate.py` - runs the test questions through RAG and the baseline and scores them
  (ROUGE-L, BERTScore, hallucination rate, two-part source citation accuracy).
  `--split holdout` runs the 9-question pilot set, `--split main` the remaining 66.
- `build_corpus.py` - compiles the CMMC/NIST QA corpus into the compliance PDFs the
  app retrieves from, grouped by control family (one PDF per family, plus KEV
  advisories and general guidance).
- `dataset/test_questions.csv` - 75 evaluation questions (question, ground_truth, difficulty).
- `documents_from_the_business/` - the 22 compiled compliance PDFs (build_corpus.py output).
- `docs/` - sample questionnaires (TPRM vendor, SOX ITGC).
- `results/` - evaluation output. `eval_*.csv` hold one row per question, `summary_*.csv`
  and `by_tier_*.csv` the means. The summaries average over every item in the split,
  refusals included; the top-level README explains how that relates to the figures
  reported in Section 4.
- `.env.example` - the two environment variables the app needs. Copy it to `.env`
  and fill in your own values.
- `.streamlit/config.toml` - turns off Streamlit's file watcher so the app starts
  without transformers/torchvision import noise in the console.

## Run
    pip install -r requirements.txt
    # in a .env file next to rag.py, set AZURE_ENDPOINT="..." and AZURE_KEY="..." (or use az login for auth)
    python build_corpus.py         # compile the compliance PDFs (once)
    python rag.py                  # chunk and index them (once)
    python evaluate.py --split holdout   # pilot run
    python evaluate.py --split main      # main evaluation
    streamlit run app.py           # the questionnaire app

The model is the `claude-opus-4-6` deployment on Azure AI Foundry (region East US2 or
Sweden Central). The endpoint is read from the `AZURE_ENDPOINT` environment variable;
`rag.py` holds the deployment name.
