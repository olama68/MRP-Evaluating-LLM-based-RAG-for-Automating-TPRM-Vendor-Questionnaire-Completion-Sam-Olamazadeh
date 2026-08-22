# MRP Evaluating LLM-based RAG for Automating TPRM Vendor Questionnaire Completion

**Author:** Sam Olamazadeh
**M.Sc. Data Science and Analytics, Toronto Metropolitan University**

Code, data, and results for the Major Research Project evaluating LLM-based
Retrieval-Augmented Generation (RAG) for automating Third-Party Risk Management
(TPRM) vendor questionnaire completion.

The repository holds the application, the corpus compilation script, the indexing and
evaluation procedure, the test set, and the per-question results, so the experiment
reported in the paper can be reproduced end to end.

## Repository structure

```
.
├── dataset/
│   ├── cmmc_train.json              # 5,104 corpus training examples
│   └── cmmc_validation.json         #   568 corpus validation examples
├── tprm_app/                        # the application and the evaluation
│   ├── rag.py                       # chunking, FAISS index, retrieval, RAG and baseline calls
│   ├── app.py                       # Streamlit questionnaire interface
│   ├── evaluate.py                  # scoring: ROUGE-L, BERTScore, faithfulness, citation accuracy
│   ├── build_corpus.py              # compiles the corpus into the retrieval PDFs
│   ├── dataset/test_questions.csv   # 75 evaluation questions (question, ground_truth, difficulty)
│   ├── documents_from_the_business/ # the 22 compiled compliance PDFs
│   ├── docs/                        # sample questionnaires
│   └── results/                     # per-question and summary evaluation output
└── eda/                             # exploratory analysis of the corpus and test set
    ├── 2026-06-21-mrp-eda.ipynb
    ├── eda_utils.py
    ├── figures/
    └── outputs/
```

## Reproducing the experiment

```bash
pip install -r tprm_app/requirements.txt
cd tprm_app
cp .env.example .env                 # then set AZURE_ENDPOINT (and AZURE_KEY, or use az login)
python build_corpus.py               # compile the retrieval PDFs (once)
python rag.py                        # chunk and index them (once)
python evaluate.py --split holdout   # 9-question pilot
python evaluate.py --split main      # main run, remaining 66 questions
streamlit run app.py                 # the questionnaire application
```

The answering model is a Claude deployment on Azure AI Foundry, named in `rag.py`.
The holdout split is drawn with a fixed seed and generation runs at temperature 0.
Retrieval and scoring are deterministic; the model calls are not strictly so, and the
pilot was run twice to show the size of that variation. See `tprm_app/results/README.md`.

## Reproducing the exploratory analysis

```bash
pip install -r eda/requirements.txt
jupyter nbconvert --to notebook --execute eda/2026-06-21-mrp-eda.ipynb \
    --output eda/2026-06-21-mrp-eda.ipynb
```

## Note on the reported figures

`tprm_app/results/summary_main.csv` averages over all 66 main questions, including the
21 the system declined to answer. Section 4 of the paper reports the 45 substantive
answers separately from those refusals, so its ROUGE-L and BERTScore figures are
higher than the ones in that file. Both are computed from the same per-question
output. `tprm_app/results/README.md` gives the mapping and the code to recompute either.

## Data

The corpus is the CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus, published by
Memoriant, Inc. under CC BY 4.0. The compiled PDFs in
`tprm_app/documents_from_the_business/` are derived from it. See `NOTICE.md`.

Code is MIT licensed. See `LICENSE`.
