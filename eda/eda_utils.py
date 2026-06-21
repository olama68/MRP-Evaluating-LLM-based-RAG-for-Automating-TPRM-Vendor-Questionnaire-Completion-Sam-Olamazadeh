from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------

# NIST SP 800-171 Rev 3 numbers each requirement as ``03.<family>.<item>``
# (e.g. 03.11.01). The middle group maps to a control family; the same families
# are labelled with the two-letter codes used by NIST SP 800-53.
NIST_171_FAMILY = {
    "01": "AC",  # Access Control
    "02": "AT",  # Awareness and Training
    "03": "AU",  # Audit and Accountability
    "04": "CM",  # Configuration Management
    "05": "IA",  # Identification and Authentication
    "06": "IR",  # Incident Response
    "07": "MA",  # Maintenance
    "08": "MP",  # Media Protection
    "09": "PS",  # Personnel Security
    "10": "PE",  # Physical Protection
    "11": "RA",  # Risk Assessment
    "12": "CA",  # Security Assessment and Authorization
    "13": "SC",  # System and Communications Protection
    "14": "SI",  # System and Information Integrity
    "15": "PL",  # Planning
    "16": "SA",  # System and Services Acquisition
    "17": "SR",  # Supply Chain Risk Management
}

FAMILY_NAMES = {
    "AC": "Access Control",
    "AT": "Awareness and Training",
    "AU": "Audit and Accountability",
    "CA": "Assessment, Authorization, and Monitoring",
    "CM": "Configuration Management",
    "CP": "Contingency Planning",
    "IA": "Identification and Authentication",
    "IR": "Incident Response",
    "MA": "Maintenance",
    "MP": "Media Protection",
    "PE": "Physical and Environmental Protection",
    "PL": "Planning",
    "PM": "Program Management",
    "PS": "Personnel Security",
    "PT": "PII Processing and Transparency",
    "RA": "Risk Assessment",
    "SA": "System and Services Acquisition",
    "SC": "System and Communications Protection",
    "SI": "System and Information Integrity",
    "SR": "Supply Chain Risk Management",
}

# Two-letter family codes recognised as standalone NIST SP 800-53 identifiers.
VALID_FAMILY_CODES = set(FAMILY_NAMES)

# Frameworks referenced across the corpus, with the regex used to detect each.
FRAMEWORK_PATTERNS = {
    "CMMC 2.0": r"CMMC",
    "NIST SP 800-171": r"800-?171",
    "NIST SP 800-172": r"800-?172",
    "NIST SP 800-53": r"800-?53(?!A)",
    "NIST SP 800-53A": r"800-?53A",
    "NIST CSF": r"\bCSF\b|cybersecurity framework",
    "HIPAA": r"HIPAA",
    "FedRAMP": r"FedRAMP",
    "CISA KEV": r"\bKEV\b|known exploited",
    "FIPS": r"\bFIPS\b",
}

# The four TPRM-relevant categories defined in the approved methodology, each
# tied to its NIST control family.
TPRM_CATEGORIES = {
    "AC": "Access Control",
    "IR": "Incident Response",
    "CM": "Configuration Management",
    "AU": "Audit",
}

# Keyword fallback used only when a text contains no control identifier.
TPRM_KEYWORDS = {
    "AC": [
        "access control", "least privilege", "authorization", "authorisation",
        "multi-factor", "multifactor", "mfa", "authenticat", "role-based",
        "rbac", "privileged account", "session lock", "identity",
    ],
    "IR": [
        "incident response", "incident handling", "incident report",
        "security incident", "breach", "forensic", "containment",
    ],
    "CM": [
        "configuration management", "baseline configuration", "configuration setting",
        "least functionality", "change control", "hardening", "configuration baseline",
    ],
    "AU": [
        "audit", "logging", "log record", "audit trail", "accountability",
        "event log", "audit record",
    ],
}

# Pre-compiled identifier patterns.
_RE_DOTTED = re.compile(r"\b0?3\.(\d{2})\.\d{2}\b")            # 800-171 Rev 3
_RE_HYPHEN = re.compile(r"\b([A-Z]{2})-\d{1,2}(?:\(\d+\))?\b")  # 800-53 style


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSON-lines file into a list of records."""
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _split_messages(messages: list[dict]) -> tuple[str, str, str]:
    """Return (system, user, assistant) text from a chat-format record."""
    parts = {"system": "", "user": "", "assistant": ""}
    for message in messages:
        parts[message.get("role", "")] = message.get("content", "")
    return parts["system"], parts["user"], parts["assistant"]


def load_corpus(data_dir: Path) -> pd.DataFrame:
    """Load the chat-format corpus into a flat data frame.

    Returns one row per example with columns ``split``, ``system``,
    ``question`` and ``answer``.
    """
    frames = []
    for split, filename in (("train", "cmmc_train.json"),
                            ("validation", "cmmc_validation.json")):
        records = _read_jsonl(Path(data_dir) / filename)
        rows = [_split_messages(rec["messages"]) for rec in records]
        frame = pd.DataFrame(rows, columns=["system", "question", "answer"])
        frame.insert(0, "split", split)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def load_test_set(csv_path: Path) -> pd.DataFrame:
    """Load the evaluation test set (question, ground_truth, difficulty)."""
    frame = pd.read_csv(csv_path)
    frame["difficulty"] = (
        frame["difficulty"].astype(str).str.strip().str.lower()
    )
    return frame


# ---------------------------------------------------------------------------
# Text characterisation
# ---------------------------------------------------------------------------

def word_count(text: str) -> int:
    """Whitespace-delimited word count."""
    return len(str(text).split())


def detect_frameworks(text: str) -> list[str]:
    """Return the compliance frameworks referenced in a text."""
    text = str(text)
    return [name for name, pattern in FRAMEWORK_PATTERNS.items()
            if re.search(pattern, text, re.IGNORECASE)]


def extract_families(text: str) -> list[str]:
    """Return NIST control-family codes referenced in a text.

    Recognises both 800-171 Rev 3 dotted identifiers (e.g. ``03.11.01``) and
    800-53 style identifiers (e.g. ``AC-2``). Order of first appearance is kept
    and duplicates are removed.
    """
    text = str(text)
    families: list[str] = []
    for group in _RE_DOTTED.findall(text):
        family = NIST_171_FAMILY.get(group)
        if family:
            families.append(family)
    for code in _RE_HYPHEN.findall(text):
        if code in VALID_FAMILY_CODES:
            families.append(code)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    return [f for f in families if not (f in seen or seen.add(f))]


def tprm_categories(text: str) -> list[str]:
    """Return every TPRM category a text maps to (multi-label).

    Control identifiers are the primary signal: a text maps to a category when
    it references that family's control identifier. Keyword matching is used
    only as a fallback when the text contains *no* control identifier at all —
    a text that references other families (for example Risk Assessment or System
    and Information Integrity) is treated as out of scope rather than guessed
    from keywords.
    """
    families = set(extract_families(text))
    labels = [name for code, name in TPRM_CATEGORIES.items() if code in families]
    if labels:
        return labels
    if families:
        return []  # references non-target families only; do not keyword-guess
    text_lower = str(text).lower()
    return [
        name for code, name in TPRM_CATEGORIES.items()
        if any(keyword in text_lower for keyword in TPRM_KEYWORDS[code])
    ]


def primary_tprm_category(text: str) -> str:
    """Return a single TPRM category for a text, or ``"Other"``.

    When a text maps to several target families, the one referenced most often
    is chosen; ties fall back to the methodology order (Access Control, Incident
    Response, Configuration Management, Audit). A text that references only
    non-target families is labelled ``"Other"``; keyword fallback applies only
    when no control identifier is present.
    """
    counts = extract_families_with_counts(text)
    ranked = [
        (code, counts[code])
        for code in TPRM_CATEGORIES
        if code in counts
    ]
    if ranked:
        ranked.sort(key=lambda item: (-item[1], list(TPRM_CATEGORIES).index(item[0])))
        return TPRM_CATEGORIES[ranked[0][0]]
    if counts:
        return "Other"  # references non-target families only
    labels = tprm_categories(text)
    return labels[0] if labels else "Other"


def extract_families_with_counts(text: str) -> dict[str, int]:
    """Return a count of control-identifier references per family."""
    text = str(text)
    counts: dict[str, int] = {}
    for group in _RE_DOTTED.findall(text):
        family = NIST_171_FAMILY.get(group)
        if family:
            counts[family] = counts.get(family, 0) + 1
    for code in _RE_HYPHEN.findall(text):
        if code in VALID_FAMILY_CODES:
            counts[code] = counts.get(code, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

PALETTE = "muted"


def set_style() -> None:
    """Apply a consistent, print-friendly figure style."""
    sns.set_theme(style="whitegrid", palette=PALETTE)
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
    })


def save_fig(fig, name: str, figures_dir: Path) -> Path:
    """Save a figure as PNG and return its path."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    out = figures_dir / f"{name}.png"
    fig.savefig(out, bbox_inches="tight")
    return out


def summary_stats(series: pd.Series) -> pd.Series:
    """Return Min / 1st Qu. / Median / Mean / 3rd Qu. / Max for a numeric series."""
    return pd.Series({
        "Min.": series.min(),
        "1st Qu.": series.quantile(0.25),
        "Median": series.median(),
        "Mean": round(series.mean(), 1),
        "3rd Qu.": series.quantile(0.75),
        "Max.": series.max(),
    })
