import os
import pickle
from pathlib import Path
import faiss
import fitz
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from anthropic import AnthropicFoundry
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Claude model on Azure AI Foundry; the endpoint comes from the environment
AZURE_ENDPOINT = os.environ.get(
    "AZURE_ENDPOINT", "https://<your-resource>.services.ai.azure.com/anthropic")
AZURE_DEPLOYMENT = "claude-opus-4-6"
MAX_TOKENS = 1024

TOP_K = 5           # passages retrieved per question
CHUNK_CHARS = 800   # characters per passage

INDEX_FILE = "rag_index.faiss"
CHUNKS_FILE = "rag_chunks.pkl"
RESULTS_DIR = "results"
DOCS_DIR = Path(__file__).resolve().parent / "documents_from_the_business"

SYSTEM_PROMPT = (
    "You are a TPRM compliance assistant. Answer ONLY using the document excerpts "
    "provided. If the answer is not in the excerpts, say 'Not found in provided "
    "documents.' Write plain prose with no markdown formatting or headings. "
    "Always end with Source: <document name, page number>.")


def get_clients():
    # API key if AZURE_KEY is set, otherwise Entra ID via az login
    key = os.environ.get("AZURE_KEY")
    if key:
        llm = AnthropicFoundry(api_key=key, base_url=AZURE_ENDPOINT)
    else:
        llm = AnthropicFoundry(
            azure_ad_token_provider=get_bearer_token_provider(
                DefaultAzureCredential(), "https://ai.azure.com/.default"),
            base_url=AZURE_ENDPOINT)
    return llm, SentenceTransformer("all-MiniLM-L6-v2")

# send one message to the model and return its text
def complete(llm, system, content, max_tokens=MAX_TOKENS):
    msg = llm.messages.create(
        model=AZURE_DEPLOYMENT, max_tokens=max_tokens, temperature=0,
        system=system, messages=[{"role": "user", "content": content}])
    return msg.content[0].text


# turn a PDF into fixed-size text chunks tagged with source and page
def pdf_to_chunks(source):
    # accepts an uploaded file or a path on disk
    if hasattr(source, "read"):
        doc, name = fitz.open(stream=source.read(), filetype="pdf"), source.name
    else:
        doc, name = fitz.open(source), Path(source).name
    chunks = []
    for page in doc:
        text = " ".join(page.get_text().split())
        for i in range(0, len(text), CHUNK_CHARS):
            piece = text[i:i + CHUNK_CHARS]
            if len(piece) >= 100:  # skip tiny leftover fragments
                chunks.append({"text": piece, "source": name, "page": page.number + 1})
    return chunks

# embed the chunks and save a FAISS index plus the chunks to disk
def build_index(chunks, embedder):
    vecs = embedder.encode([c["text"] for c in chunks]).astype("float32")
    index = faiss.IndexFlatL2(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, INDEX_FILE)
    pickle.dump(chunks, open(CHUNKS_FILE, "wb"))

# read the saved index and chunks back from disk
def load_index():
    return faiss.read_index(INDEX_FILE), pickle.load(open(CHUNKS_FILE, "rb"))

# embed the question and return the TOP_K nearest chunks
def retrieve(question, index, chunks, embedder):
    q = embedder.encode([question]).astype("float32")
    _, ids = index.search(q, TOP_K)
    return [chunks[i] for i in ids[0]]

# retrieve context for the question and answer from it, returning citations
def ask_rag(question, index, chunks, llm, embedder, hits=None):
    if hits is None:
        hits = retrieve(question, index, chunks, embedder)
    context = "\n\n".join(f"[{h['source']} p.{h['page']}]\n{h['text']}" for h in hits)
    answer = complete(llm, SYSTEM_PROMPT,
                      f"Excerpts:\n{context}\n\nQuestion: {question}")
    citations = [{"source": h["source"], "page": h["page"],
                  "excerpt": h["text"][:300]} for h in hits]
    return answer, citations

# answer the question directly, with no retrieved context (comparison baseline)
def ask_baseline(question, llm):
    return complete(llm, "You are a TPRM compliance assistant.", question)


if __name__ == "__main__":
    # index the compiled compliance PDFs
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    chunks = []
    for pdf in sorted(DOCS_DIR.glob("*.pdf")):
        chunks.extend(pdf_to_chunks(pdf))
    build_index(chunks, embedder)
    print(f"indexed {len(chunks)} chunks from {DOCS_DIR.name}")
