# MRP Evaluating LLM-based RAG for Automating TPRM Vendor Questionnaire Completion

**Author:** Sam Olamazadeh

Exploratory Data Analysis for the Major Research Project (MRP) evaluating
LLM-based Retrieval-Augmented Generation (RAG) for automating Third-Party Risk
Management (TPRM) vendor questionnaire completion.

## Repository structure

```
.
├── dataset/
│   ├── cmmc_train.json          # 5,104 corpus training examples
│   └── cmmc_validation.json     #   568 corpus validation examples
├── tprm_app/
│   └── dataset/
│       └── test_questions.csv   # 75 evaluation questions (question, ground_truth, difficulty)
└── eda/
    ├── 2026-06-21-mrp-eda.ipynb # Main EDA notebook
    ├── eda_utils.py             # Reusable helpers (loaders, tagging, plot styling)
    ├── requirements.txt         # Python dependencies
    ├── figures/                 # Generated figures (PNG)
    └── outputs/                 # Generated summary tables (CSV) and findings
```

## Reproducing the analysis

```bash
pip install -r eda/requirements.txt
jupyter notebook eda/2026-06-21-mrp-eda.ipynb
```

Or to run non-interactively:

```bash
jupyter nbconvert --to notebook --execute eda/2026-06-21-mrp-eda.ipynb \
    --output eda/2026-06-21-mrp-eda.ipynb
```

## Data

The corpus is the **CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus** (CC-BY-4.0),
stored in chat format (system / user / assistant message triples).
The test set comprises 75 TPRM-relevant questions balanced across three difficulty
levels (easy / medium / hard).
