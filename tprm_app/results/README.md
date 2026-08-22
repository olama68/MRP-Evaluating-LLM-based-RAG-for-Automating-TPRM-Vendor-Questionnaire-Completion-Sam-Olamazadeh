# Evaluation results

Output of `evaluate.py`. The 75 test questions are split into a 9 question pilot
(3 per difficulty tier, drawn with `SEED = 8012`) and the remaining 66, which form
the main run.

| File | Contents |
|------|----------|
| `eval_main.csv` | Per question output for the 66 main questions: both answers, the cited document, and every metric column. |
| `summary_main.csv` | Metric means over all 66 main questions. |
| `by_tier_main.csv` | The same means split by difficulty tier. |
| `eval_holdout.csv` | Per question output for the 9 pilot questions. |
| `summary_holdout.csv`, `by_tier_holdout.csv` | Means over the 9 pilot questions. |
| `eval_holdout_run1.csv`, `summary_holdout_run1.csv` | The first pilot run. The pilot was run twice on the same nine questions; both are kept so the run to run variation is visible. |

## Which questions each number covers

This matters when comparing these files against the report.

`summary_main.csv` and `by_tier_main.csv` average over **all 66** main questions.
Twenty one of those are refusals, where the model returned "Not found in provided
documents" because retrieval surfaced no supporting passage. A refusal makes no
claim, so it is scored 0 on ROUGE-L and low on BERTScore against a substantive
reference answer.

Section 4 of the report separates the two populations and reports the **45
substantive answers** apart from the 21 refusals, because the quality of an answer
the system chose not to give is not a meaningful quantity. Both sets of figures come
from the same `eval_main.csv`:

| | All 66 | Substantive 45 |
|---|---|---|
| ROUGE-L (RAG) | 0.262 | 0.366 |
| BERTScore (RAG) | 0.848 | 0.865 |
| Faithfulness (RAG) | 0.758 | 0.788 |
| ROUGE-L (baseline) | 0.146 | 0.150 |

Refusals by tier: 9 easy, 9 medium, 3 hard.

To reproduce either column from the per question file:

```python
import pandas as pd
df = pd.read_csv("eval_main.csv")
print(df.rag_rouge_l.mean())                  # all 66
print(df[~df.not_found].rag_rouge_l.mean())   # substantive 45
```

## Column notes

- `not_found` marks a refusal.
- `rag_support` and `baseline_support` are the RAGAS style faithfulness scores, the
  share of answer sentences the retrieved passages support.
- `rag_hallucinated` is set when support falls below 0.5. Refusals are excluded, so
  the RAG hallucination rate is 0 by construction for those rows.
- `cite_named` records whether the answer named a source document, `cite_supported`
  whether that document's passages back the answer. Both are reported over answered
  questions only.
- The retrieved passage text is dropped before writing these files, so the `context`
  and `cited_text` columns used during scoring do not appear here. Rerunning
  `evaluate.py` regenerates them.
