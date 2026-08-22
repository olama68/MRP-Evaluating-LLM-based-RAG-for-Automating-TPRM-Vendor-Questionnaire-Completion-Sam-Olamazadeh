import os
import re
import pandas as pd
import fitz
import streamlit as st
import rag


@st.cache_resource
def clients():
    return rag.get_clients()


def extract_questions(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    # split on numbered markers like 1. 2) Q3 2.2.1, then join the wrapped
    # lines of each item back into one question
    marker = re.compile(r'(?m)^[ \t]*(Q?\d+(?:\.\d+)*)[.)]?[ \t]+')
    marks = list(marker.finditer(text))
    questions = []
    for i, m in enumerate(marks):
        label, start = m.group(1), m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        nxt = marks[i + 1].group(1) if i + 1 < len(marks) else ""
        if nxt.startswith(label + "."):      # section header, its children follow
            continue
        body = " ".join(text[start:end].split())
        body = re.sub(r"\s*Response:.*$", "", body, flags=re.I).strip()
        if len(body) > 15:
            questions.append(body)
    # fallback for unnumbered files: join wrapped lines up to each question mark
    if len(questions) < 2:
        questions, buf = [], []
        for line in text.splitlines():
            buf.append(line.strip())
            if line.rstrip().endswith("?"):
                q = " ".join(" ".join(buf).split())
                if len(q) > 15:
                    questions.append(q)
                buf = []
    return questions


st.set_page_config(page_title="TPRM Chatbot", layout="wide")
st.title("TPRM Chatbot")
st.caption("RAG compliance questionnaire assistant")

llm, embedder = clients()

with st.sidebar:
    st.header("Compliance documents")
    doc_pdfs = st.file_uploader("Upload source PDFs", type="pdf",
                                accept_multiple_files=True, key="docs")
    if doc_pdfs and st.button("Index documents", type="primary"):
        chunks = []
        for f in doc_pdfs:
            chunks.extend(rag.pdf_to_chunks(f))
        rag.build_index(chunks, embedder)
        st.success(f"{len(chunks)} chunks from {len(doc_pdfs)} file(s)")

    st.header("Questionnaire")
    q_pdf = st.file_uploader("Upload questionnaire PDF", type="pdf", key="questionnaire")
    if q_pdf and st.button("Load questions"):
        st.session_state.questions = extract_questions(q_pdf)
        st.session_state.recs = {}
        st.success(f"{len(st.session_state.questions)} question(s) loaded")

questions = st.session_state.get("questions", [])
recs = st.session_state.get("recs", {})

if not questions:
    st.info("Upload a questionnaire to get started.")
    st.stop()

if st.button("Run all", type="primary", disabled=not os.path.exists(rag.INDEX_FILE)):
    index, chunks = rag.load_index()
    for q in questions:
        if q not in recs:
            recs[q] = rag.ask_rag(q, index, chunks, llm, embedder)
    st.session_state.recs = recs

for i, q in enumerate(questions, 1):
    st.markdown(f"**Q{i}.** {q}")
    if q in recs:
        answer, citations = recs[q]
        st.write(answer)
        with st.expander("Sources"):
            for c in citations:
                st.caption(f"{c['source']} p.{c['page']}: {c['excerpt']}...")

if recs:
    rows = [{"question": q, "answer": recs[q][0],
             "top_source": recs[q][1][0]["source"] if recs[q][1] else "",
             "top_page": recs[q][1][0]["page"] if recs[q][1] else ""}
            for q in questions if q in recs]
    st.download_button("Download CSV", pd.DataFrame(rows).to_csv(index=False),
                       "tprm_recommendations.csv", "text/csv")
