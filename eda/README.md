# Exploratory Data Analysis: RAG for TPRM Vendor Questionnaire Completion

Exploratory data analysis for the MRP *Evaluating LLM-based RAG for Automating TPRM
Vendor Questionnaire Completion*. The analysis characterises two inputs to the
evaluation:

1. **Knowledge corpus**: the CMMC 2.0 / NIST SP 800-171 compliance QA corpus
   (5,672 question-answer examples), used as the retrieval knowledge base.
2. **Test set**: 75 TPRM-relevant evaluation questions with ground-truth answers,
   balanced across three difficulty levels.

## Contents

| Path | Description |
|------|-------------|
| `2026-06-21-mrp-eda.ipynb` | Main EDA notebook: volume, length distributions, term/n-gram analysis, and framework / control-family / TPRM-category coverage. |
| `eda_utils.py` | Reusable helpers: data loaders, framework and NIST control-family tagging, TPRM-category mapping, and plot styling. |
| `figures/` | Generated figures (PNG). |
| `outputs/` | Generated summary tables (CSV). |
| `requirements.txt` | Python dependencies. |

## Data layout (expected)

The notebook reads from the project `dataset/` and `tprm_app/` folders by default:

```
MRP/
├── dataset/
│   ├── cmmc_train.json          # 5,104 examples (JSONL: {"messages": [...]})
│   └── cmmc_validation.json     #   568 examples
├── tprm_app/
│   └── dataset/test_questions.csv   # 75 questions: question, ground_truth, difficulty
└── eda/                          # this folder
```

Paths are set at the top of the notebook via the `DATA_DIR` variable; adjust if the
layout differs.

## Reproducing

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute 2026-06-21-mrp-eda.ipynb \
    --output 2026-06-21-mrp-eda.ipynb
```

All figures and summary tables are written to `figures/` and `outputs/`.

## Data source

CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus (CC-BY-4.0). The corpus is stored in
chat format; each record is a system / user / assistant message triple.
