# MRP Evaluating LLM-based RAG for Automating TPRM Vendor Questionnaire Completion

**Sam Olamazadeh**
M.Sc. Data Science and Analytics, Toronto Metropolitan University

This repository holds the data, code, and results behind the Major Research Project of
the same name. It is the reference implementation for the reported experiment, so the
figures in the paper can be traced back to the per-question output that produced them.

## The study

Third-party risk management requires organizations to assess vendor security posture by
completing standardized compliance questionnaires. For each field an analyst must locate
the relevant passage across hundreds of pages of regulatory text, extract a defensible
answer, and record its source. A single vendor review can occupy an experienced analyst
for several days, and organizations maintain hundreds of active vendor relationships at
once.

The study evaluates whether a bounded, off-the-shelf Retrieval-Augmented Generation
(RAG) tool can do that work reliably enough to be used in practice. Bounded means the
tool answers only from content retrieved out of the compliance documents supplied with
the questionnaire, and declines when the retrieved passages do not support an answer.
It is compared against direct prompting of the same language model with no document
context, on identical questions, so that what retrieval contributes can be separated
from what the model contributes on its own.

## Research questions

1. **RQ1.** How accurately does a bounded, off-the-shelf RAG tool answer compliance
   questions drawn from TPRM questionnaire fields, and does that accuracy vary with
   question difficulty?
2. **RQ2.** Does the retrieval-augmented condition produce more accurate and less
   hallucinated answers than direct prompting of the same model without documents?
3. **RQ3.** How accurately does the tool cite its sources, and do citations hold when
   the same content appears in more than one document?
4. **RQ4.** What are the practical limitations, and under what conditions does automated
   generation fall short of acceptable accuracy?
5. **RQ5.** What proportion of generated answers does a human domain expert judge
   factually correct and appropriately cited, and how does that compare with the
   automated measures?

## Method in brief

The knowledge base is the CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus (5,672
question-answer pairs). Its answer text is compiled into 22 PDFs grouped by NIST control
family, with the corpus questions stripped out so that retrieval must find answer
content rather than match a question string. Those PDFs are chunked into contiguous
800-character passages, embedded, and indexed; each question retrieves the five nearest
passages.

The test set is 75 questions with reference answers, balanced across three difficulty
tiers. Nine are held out as a pilot with a fixed seed; the remaining 66 form the main
run. Both conditions see the same questions. Answers are scored on lexical overlap
(ROUGE-L), semantic similarity (BERTScore), faithfulness to the retrieved evidence, a
hallucination rate derived from it, and a two-part source-citation accuracy: whether the
answer names a document retrieval actually returned, and whether that document holds
passages supporting the answer given. A domain practitioner then reviews a nine-answer
sample against the automated scores.

## Results

Main run, 66 questions, means on a 0 to 1 scale.

| Measure | Retrieval-augmented | Baseline |
|---|---|---|
| ROUGE-L | 0.262 | 0.146 |
| BERTScore | 0.848 | 0.814 |
| Faithfulness | 0.758 | 0.135 |
| Hallucination rate | 0.000 | 0.970 |
| Source citation named | 0.956 | not applicable |
| Source citation supported | 0.933 | not applicable |

Retrieval improved every measure, but unevenly. The gap on faithfulness, 0.623, is about
five times the gap on ROUGE-L, 0.116, and larger still against BERTScore, 0.034. What
retrieval supplies is grounding, not fluency: 64 of the 66 baseline answers count as
hallucinations, and none of the retrieval-augmented answers do.

**The zero hallucination rate has a price.** The system returned substantive answers for
45 of the 66 questions and declined the other 21, or 31.8 percent, on the grounds that
the retrieved passages did not support an answer. Refusals make no claim, so they are
not hallucinations, but they score zero on the reference-based measures. Excluding them
raises ROUGE-L from 0.262 to 0.366 and BERTScore from 0.848 to 0.865.

| Measure | Easy | Medium | Hard | All tiers |
|---|---|---|---|---|
| Items refused | 9 | 9 | 3 | 21 |
| Substantive answers | 13 | 13 | 19 | 45 |
| ROUGE-L (all items) | 0.235 | 0.180 | 0.372 | 0.262 |
| ROUGE-L (substantive) | 0.377 | 0.272 | 0.422 | 0.366 |
| BERTScore (substantive) | 0.866 | 0.853 | 0.872 | 0.865 |
| Faithfulness | 0.713 | 0.769 | 0.793 | 0.758 |
| Citation (named / supported) | 12 / 12 | 12 / 11 | 19 / 19 | 43 / 42 |

The hard tier refused least, which the design did not anticipate. The explanation is its
composition rather than better retrieval: 17 of its 22 questions name a specific
published vulnerability whose identifier appears verbatim in the source document. Among
the five hard questions that genuinely require evidence across documents, two were
refused, matching the other tiers. Failures concentrated instead in questions asking for
an artifact the corpus does not hold, and in questions whose own wording carries the
truncation and character corruption the corpus inherited from PDF extraction.

**Expert validation.** A practitioner reviewed nine substantive answers, three per tier.
Seven were judged factually correct, correctly cited, and acceptable for submission,
77.8 percent on each criterion. None was judged outright incorrect; the two that failed
were partially correct and both fell in the medium tier. The automated citation measure
passed all nine. Both disagreements arose the same way: retrieval returned passages the
answer then used faithfully, while the passage actually holding the evidence was never
retrieved. One of the two rejected answers recorded the highest faithfulness of the
nine, 0.92. On this sample the automated measures overstate citation quality.

A repeat pass over the holdout moved no retrieval-augmented measure by more than 0.028,
so these figures do not rest on a single run.

## Conclusion

Bounded retrieval-augmented generation is worth deploying on this task, but as a
drafting instrument under human review rather than an unsupervised answering system. On
a hundred-field questionnaire it would return roughly 68 grounded and cited drafts and
decline the remaining 32, against the several analyst days such a review currently
consumes. Because roughly one returned answer in five did not survive expert scrutiny,
the analyst's effort is displaced from writing answers to verifying the evidence behind
them rather than removed. A deployment that skipped that verification would be worse
than the manual process it replaces, because it would produce attestations that look
defensible and are not.

The finding that bears most on safety is the residual failure the standard measures
cannot see: an answer faithful to evidence that was wrongly retrieved. Two priorities
follow, a larger multi-rater expert validation, and a measure of retrieval adequacy.

## Which questions each reported number covers

`tprm_app/results/summary_main.csv` and `by_tier_main.csv` average over **all 66** main
questions, with the 21 refusals scored as zero. Section 4 of the paper reports the **45
substantive** answers separately, because the quality of an answer the system chose not
to give is not a meaningful quantity. Both come from the same per-question file, so
either is reproducible from it:

```python
import pandas as pd
df = pd.read_csv("tprm_app/results/eval_main.csv")
print(df.rag_rouge_l.mean())                  # 0.262, all 66
print(df[~df.not_found].rag_rouge_l.mean())   # 0.366, substantive 45
```

`eval_holdout_run1.csv` and `eval_holdout.csv` are the two passes over the same nine
pilot questions, kept so the run to run variation is visible.

## Repository layout

```
.
├── dataset/                         # the knowledge corpus, 5,672 QA pairs
├── tprm_app/                        # the application and the evaluation
│   ├── rag.py                       # chunking, index, retrieval, both conditions
│   ├── evaluate.py                  # the four measures and the run splits
│   ├── build_corpus.py              # compiles the corpus into the 22 retrieval PDFs
│   ├── app.py                       # Streamlit questionnaire interface
│   ├── dataset/test_questions.csv   # the 75 test questions with reference answers
│   ├── documents_from_the_business/ # the 22 compiled retrieval PDFs
│   ├── docs/                        # sample questionnaires
│   └── results/                     # per-question and summary output
└── eda/                             # corpus and test-set characterisation (Section 3.2)
    ├── 2026-06-21-mrp-eda.ipynb
    ├── figures/                     # the Appendix B figures
    └── outputs/                     # summary tables and written findings
```

`tprm_app/README.md` documents the application itself and its run commands.

## Reproducing the experiment

```bash
pip install -r tprm_app/requirements.txt
cd tprm_app
cp .env.example .env                 # set AZURE_ENDPOINT, and AZURE_KEY or use az login
python build_corpus.py               # compile the retrieval PDFs (once)
python rag.py                        # chunk and index them (once)
python evaluate.py --split holdout   # nine-question pilot
python evaluate.py --split main      # main run, the remaining 66
```

The answering model is a Claude deployment on Azure AI Foundry, named in `rag.py`.
Generation runs at temperature 0 and the holdout split is drawn with a fixed seed.
Retrieval and scoring are deterministic; the model calls are not strictly so, which is
why the pilot was run twice.

The exploratory analysis is reproduced separately:

```bash
pip install -r eda/requirements.txt
jupyter nbconvert --to notebook --execute eda/2026-06-21-mrp-eda.ipynb \
    --output eda/2026-06-21-mrp-eda.ipynb
```

## Data and rights

The corpus is the CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus, published by
Memoriant, Inc. under CC BY 4.0. The compiled PDFs in
`tprm_app/documents_from_the_business/` are derived from it. See `NOTICE.md`.

The code is copyright (c) 2026 Sam Olamazadeh, all rights reserved. It is
published so that the reported experiment can be examined and reproduced; no
licence to reuse it is granted.
