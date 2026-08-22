import argparse
import os
import re
import pandas as pd
from rouge_score import rouge_scorer
from bert_score import score as bert_score
from rag import (ask_rag, ask_baseline, complete, load_index, get_clients,
                 retrieve, RESULTS_DIR)

SEED = 8012 # random seed for reproducibility of the holdout split
HOLDOUT_PER_TIER = 3 # number of questions per difficulty tier to hold out for evaluation
NOT_FOUND = "Not found in provided documents"

# ROUGE-L scorer with stemming
SCORER = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

# Prompt for judging whether the retrieved passages support the answer sentences.
JUDGE_PROMPT = (
    "You will be given document passages and the numbered sentences of an answer. "
    "For each sentence decide whether the passages fully support it. Reply with "
    "one line per sentence in the form '1: yes' or '1: no' and nothing else.")

# hold out a fixed number of questions per difficulty tier for the pilot split
def pick_split(df, split):
    # 3 questions per tier are held out as the pilot / stability set
    holdout = df.groupby("difficulty").sample(HOLDOUT_PER_TIER, random_state=SEED)
    if split == "holdout":
        return holdout
    if split == "main":
        return df.drop(holdout.index)
    return df

# ROUGE-L F-measure between a predicted answer and the reference
def rouge_l(pred, ref):
    return SCORER.score(ref, pred)["rougeL"].fmeasure

# pull the document name from the last "Source:" line in an answer
def cited_doc(answer):
    hits = re.findall(r"Source:\s*(.+)", answer)
    return hits[-1].strip() if hits else ""

# split text into sentences longer than 20 characters
def sentences(text):
    text = re.sub(r"[#*|`]", " ", str(text))
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]

def supported_fraction(llm, answer, context):
    # RAGAS style faithfulness: the share of answer sentences the retrieved
    # passages support, judged by the model
    sents = sentences(answer)
    if not sents or not str(context).strip():
        return 0.0
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sents))
    reply = complete(llm, JUDGE_PROMPT,
                     f"Passages:\n{context}\n\nAnswer sentences:\n{numbered}",
                     max_tokens=300)
    verdicts = re.findall(r"\d+\s*:\s*(yes|no)", reply.lower())
    return verdicts.count("yes") / len(verdicts) if verdicts else 0.0


def run(questions_csv, split):
    df = pick_split(pd.read_csv(questions_csv), split)
    llm, embedder = get_clients()
    index, chunks = load_index()

    rows = []
    for _, q in df.iterrows():
        # scoring uses the full passages, not the 300 character display excerpts,
        # so retrieve once and share the hits with ask_rag
        hits = retrieve(q["question"], index, chunks, embedder)
        rag_ans, _ = ask_rag(q["question"], index, chunks, llm, embedder, hits=hits)
        base_ans = ask_baseline(q["question"], llm)
        cited = cited_doc(rag_ans)
        cited_text = "\n\n".join(h["text"] for h in hits if h["source"] in cited)
        rows.append({"question": q["question"], "ground_truth": q["ground_truth"],
                     "difficulty": q["difficulty"], "rag_answer": rag_ans,
                     "baseline_answer": base_ans,
                     "context": "\n\n".join(h["text"] for h in hits),
                     "not_found": rag_ans.startswith(NOT_FOUND),
                     "cited_doc": cited,
                     "cited_text": cited_text,
                     "cite_named": bool(cited_text)})
    out = pd.DataFrame(rows)
    # Compute evaluation metrics for both RAG and baseline answers, including ROUGE-L and BERTScore.
    out["rag_rouge_l"] = [rouge_l(r, g) for r, g in zip(out.rag_answer, out.ground_truth)]
    out["baseline_rouge_l"] = [rouge_l(r, g) for r, g in zip(out.baseline_answer, out.ground_truth)]
    # Bert (precision, recall, F1)
    _, _, rag_f = bert_score(out.rag_answer.tolist(), out.ground_truth.tolist(), lang="en")
    _, _, base_f = bert_score(out.baseline_answer.tolist(), out.ground_truth.tolist(), lang="en")
    out["rag_bertscore"] = rag_f.tolist()
    out["baseline_bertscore"] = base_f.tolist()

    # an answer counts as a hallucination when most of its sentences lack
    # support in the retrieved passages; a refusal makes no claim, so it is not one
    out["rag_support"] = [supported_fraction(llm, a, c)
                          for a, c in zip(out.rag_answer, out.context)]
    out["baseline_support"] = [supported_fraction(llm, a, c)
                               for a, c in zip(out.baseline_answer, out.context)]
    out["rag_hallucinated"] = out.rag_support < 0.5
    out.loc[out.not_found, "rag_hallucinated"] = False
    out["baseline_hallucinated"] = out.baseline_support < 0.5

    # citation dimension 2: do the cited document's passages back the answer
    sup = [supported_fraction(llm, a, c)
           for a, c in zip(out.rag_answer, out.cited_text)]
    out["cite_supported"] = [s >= 0.5 and n for s, n in zip(sup, out.cite_named)]

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out.drop(columns=["context", "cited_text"]).to_csv(
        f"{RESULTS_DIR}/eval_{split}.csv", index=False)

    answered = out[~out.not_found]
    summary = pd.DataFrame(
        {"rag": [out.rag_rouge_l.mean(), out.rag_bertscore.mean(),
                 out.rag_support.mean(), out.rag_hallucinated.mean(),
                 answered.cite_named.mean(), answered.cite_supported.mean()],
         "baseline": [out.baseline_rouge_l.mean(), out.baseline_bertscore.mean(),
                      out.baseline_support.mean(),
                      out.baseline_hallucinated.mean(), None, None]},
        index=["rouge_l", "bertscore", "faithfulness", "hallucination_rate",
               "citation_named", "citation_supported"]).round(3)
    summary.to_csv(f"{RESULTS_DIR}/summary_{split}.csv")
    print(f"Split: {split} ({len(out)} questions)")
    print(summary)
    print(f"\nNot found answers: {out.not_found.sum()} of {len(out)}")

    tier_cols = ["rag_rouge_l", "baseline_rouge_l", "rag_bertscore",
                 "baseline_bertscore", "rag_hallucinated", "cite_named", "cite_supported"]
    by_tier = out.groupby("difficulty")[tier_cols].mean().round(3)
    by_tier.to_csv(f"{RESULTS_DIR}/by_tier_{split}.csv")
    print("\nBy difficulty:")
    print(by_tier)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="dataset/test_questions.csv")
    parser.add_argument("--split", default="holdout", choices=["holdout", "main", "all"])
    args = parser.parse_args()
    run(args.questions, args.split)
