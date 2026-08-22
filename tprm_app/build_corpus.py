import json
import re
import textwrap
from collections import Counter
from pathlib import Path
import fitz

DATA_DIR = Path(__file__).resolve().parent.parent / "dataset"
OUT_DIR = Path(__file__).resolve().parent / "documents_from_the_business"

# NIST SP 800-171 Rev 3 numbers each requirement 03.<family>.<item>;
# the middle group maps to a control family
NIST_171_FAMILY = {
    "01": "AC", "02": "AT", "03": "AU", "04": "CM", "05": "IA", "06": "IR",
    "07": "MA", "08": "MP", "09": "PS", "10": "PE", "11": "RA", "12": "CA",
    "13": "SC", "14": "SI", "15": "PL", "16": "SA", "17": "SR",
}

FAMILY_NAMES = {
    "AC": "Access Control", "AT": "Awareness and Training",
    "AU": "Audit and Accountability", "CA": "Assessment and Authorization",
    "CM": "Configuration Management", "CP": "Contingency Planning",
    "IA": "Identification and Authentication", "IR": "Incident Response",
    "MA": "Maintenance", "MP": "Media Protection",
    "PE": "Physical Protection", "PL": "Planning", "PM": "Program Management",
    "PS": "Personnel Security", "PT": "PII Processing and Transparency",
    "RA": "Risk Assessment", "SA": "System and Services Acquisition",
    "SC": "System and Communications Protection",
    "SI": "System and Information Integrity",
    "SR": "Supply Chain Risk Management",
}

RE_DOTTED = re.compile(r"\b0?3\.(\d{2})\.\d{2}\b")
RE_HYPHEN = re.compile(r"\b([A-Z]{2})-\d{1,2}(?:\(\d+\))?\b")
RE_GLYPH = re.compile(r"GLYPH\(cmap:[^)]*\)")

WRAP = 100
LINES_PER_PAGE = 60


def clean(text):
    text = RE_GLYPH.sub(" ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def load_entries():
    entries, seen = [], set()
    for name in ("cmmc_train.json", "cmmc_validation.json"):
        for line in open(DATA_DIR / name, encoding="utf-8"):
            if not line.strip():
                continue
            msgs = {m["role"]: m["content"] for m in json.loads(line)["messages"]}
            key = (msgs.get("user", "").strip(), msgs.get("assistant", "").strip())
            if key[0] and key[1] and key not in seen:
                seen.add(key)
                entries.append((clean(key[0]), clean(key[1])))
    return entries


def primary_family(text):
    counts = Counter(NIST_171_FAMILY[g] for g in RE_DOTTED.findall(text)
                     if g in NIST_171_FAMILY)
    counts.update(c for c in RE_HYPHEN.findall(text) if c in FAMILY_NAMES)
    return counts.most_common(1)[0][0] if counts else ""


def group_name(question, answer):
    if "cve-" in question.lower():
        return "CISA KEV Vulnerability Advisories"
    code = primary_family(question + " " + answer)
    if code:
        return "Security Controls " + FAMILY_NAMES[code]
    return "General Compliance Guidance"


def write_pdf(path, entries):
    # only the answer text goes into the document; the questions are kept out
    # so the compiled PDFs read like business documents, not a QA dump, and
    # retrieval cannot succeed by matching a test question word for word
    lines = []
    for _, answer in entries:
        lines += textwrap.wrap(answer, WRAP) + [""]
    doc = fitz.open()
    for i in range(0, len(lines), LINES_PER_PAGE):
        page = doc.new_page()
        page.insert_text((50, 50), "\n".join(lines[i:i + LINES_PER_PAGE]), fontsize=9)
    pages = doc.page_count
    doc.save(path)
    doc.close()
    return pages


def main():
    OUT_DIR.mkdir(exist_ok=True)
    groups = {}
    for question, answer in load_entries():
        groups.setdefault(group_name(question, answer), []).append((question, answer))
    for name, entries in sorted(groups.items()):
        out = OUT_DIR / (name.replace(" ", "_") + ".pdf")
        pages = write_pdf(out, entries)
        print(f"{out.name}: {len(entries)} entries, {pages} pages")


if __name__ == "__main__":
    main()
