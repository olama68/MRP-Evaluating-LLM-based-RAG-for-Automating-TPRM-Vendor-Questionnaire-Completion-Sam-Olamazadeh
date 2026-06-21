# EDA — Summary of Findings

Exploratory analysis of the two inputs to the RAG-for-TPRM evaluation: the CMMC 2.0
/ NIST SP 800-171 knowledge corpus and the 75-question evaluation test set. Figure
numbers refer to `2026-06-21-mrp-eda.ipynb` and `figures/`.

## Knowledge corpus

The corpus holds **5,672** question–answer pairs (**5,104** train, **568**
validation), stored in chat format with a single shared system prompt. Questions
are short (median **14** words) and answers are long and detailed (median **116**
words, mean **209**, maximum **1,094**), consistent with retrieval-oriented QA where
a concise query maps to a citable, multi-sentence answer (Figure 1). The
document–term matrix over answers contains **17,788** distinct terms; term
frequency, the word cloud, and *n*-gram analysis (Figures 2–4) confirm the
vocabulary is dominated by security-control language — *security*, *control*,
*system*, *requirements*, and fixed phrases such as *access control*,
*configuration management*, and *organization-defined parameter*.

Framework coverage (Figure 6) is led by NIST SP 800-53, SP 800-171, and CMMC 2.0,
with supporting coverage of FedRAMP, HIPAA, and the CISA KEV catalogue. All
eighteen NIST control families appear (Figure 7); System and Information Integrity
(SI), Access Control (AC), and System and Communications Protection (SC) are the
most heavily represented. The four families that anchor the methodology — Access
Control, Audit and Accountability, Configuration Management, and Incident Response —
are all well covered, so the knowledge base can in principle support the targeted
questionnaire items. Of the 5,672 records, **3,785** questions are unique;
the remainder are repeated questions (typically paired with different answers).

## Test set

The 75-question test set is balanced by design — **25 easy, 25 medium, 25 hard**
(Figure 8) — with ground-truth length rising with difficulty (hard items include
CVE / vulnerability-management questions carrying the longest reference answers).
Questions are short (median **15** words) and reference answers moderate (median
**94** words).

Two findings carry methodological weight.

**1. Category scope.** Tagging each question by NIST control family and mapping to
the four declared TPRM categories, only **20 of 75** questions fall inside the
target categories (Access Control 12, Audit 5, Incident Response 2, Configuration
Management 1); the remaining **55** reference other domains, predominantly Risk
Assessment (RA) and System and Information Integrity (SI) (Figures 9–10). The test
set, as currently built, is therefore broader than the methodology's stated focus.
Its control-family mix also diverges from the corpus, over-weighting RA and SI and
under-weighting families the corpus emphasises such as SC and SR (Figure 11). A
decision is needed before the evaluation runs: either re-scope the test set toward
the four categories, or widen the methodology's category framing to match the
broader coverage the current set exercises.

**2. Corpus–test overlap (leakage).** **70 of 75** test questions appear verbatim in
the corpus and **all 75** are near-duplicates (TF-IDF cosine ≈ 1.0), yet only **1 of
75** ground-truth answers reproduces the corresponding corpus answer (Figure 12).
The questions were thus drawn from the knowledge base while the reference answers
were curated independently. Two consequences follow. Because the questions are in
the knowledge base, the retriever can locate a highly relevant passage for nearly
every item, so the evaluation measures retrieval-and-synthesis over *seen* material
rather than generalisation to unseen questions. Because the reference answers are
not the stored corpus answers, the task is not a trivial lookup and the metrics
remain meaningful. Both points should be stated explicitly in the methodology and
discussion and reported alongside the ROUGE-L and BERTScore results.

## Implications for the evaluation

- Resolve the test-set scope against the methodology before scoring.
- Report the leakage characteristics so the RAG-versus-baseline gap is interpreted
  as performance on in-distribution questions.
- The corpus comfortably covers the four target families, so a re-scoped test set
  concentrated on them is feasible without changing the knowledge base.
