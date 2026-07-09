#!/usr/bin/env python3
"""
Compute and plot FOMC references to AI or artificial intelligence.

Counts references in cached minutes/transcript PDFs and Federal Reserve
statement HTML pages, then creates a stacked column chart by meeting.
"""

import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from html.parser import HTMLParser
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, YearLocator
import pdfplumber
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
MINUTES_DIR = BASE_DIR / "data" / "minutes"
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
STATEMENTS_DIR = BASE_DIR / "data" / "statements"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DATA = BASE_DIR / "data" / "ai_mentions.csv"
OUTPUT_PLOT = OUTPUT_DIR / "fomc_ai_mentions_stacked.png"

STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary{date}a.htm"
REQUEST_HEADERS = {
    "User-Agent": "press-minutes-parser/1.0 (+https://www.federalreserve.gov/)",
}

AI_PATTERNS = [
    re.compile(r"\bartificial[-\s]+intelligence\b", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9.])(?:AI|A\.I\.)(?![A-Za-z0-9.])"),
]


class StatementHTMLParser(HTMLParser):
    """Extract statement body paragraphs from a Federal Reserve press release page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_article = False
        self.in_paragraph = False
        self.paragraph_class = ""
        self.current_text = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "div" and attrs_dict.get("id") == "article":
            self.in_article = True
        elif tag == "div" and attrs_dict.get("id") == "lastUpdate":
            self.in_article = False

        if self.in_article and tag == "p":
            self.in_paragraph = True
            self.paragraph_class = attrs_dict.get("class", "")
            self.current_text = []

    def handle_endtag(self, tag):
        if self.in_article and self.in_paragraph and tag == "p":
            text = normalize_text(" ".join(self.current_text))
            if text:
                self.paragraphs.append((text, self.paragraph_class))
            self.in_paragraph = False
            self.paragraph_class = ""
            self.current_text = []

    def handle_data(self, data):
        if self.in_article and self.in_paragraph:
            self.current_text.append(data)


def normalize_text(text):
    """Normalize whitespace in extracted text."""
    return re.sub(r"\s+", " ", text).strip()


def count_ai_references(text):
    """Count references to AI, A.I., or artificial intelligence."""
    return sum(len(pattern.findall(text)) for pattern in AI_PATTERNS)


def extract_date_from_filename(filename):
    """Extract date from filename like FOMCpresconf20200129.pdf -> 2020-01-29."""
    match = re.search(r"(\d{8})", filename)
    if not match:
        return None

    date_str = match.group(1)
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def compact_date(date_str):
    """Convert YYYY-MM-DD to YYYYMMDD."""
    return date_str.replace("-", "")


def load_dates_from_pdf_dirs():
    """Return sorted meeting dates covered by the local document cache."""
    dates = set()
    for directory in (MINUTES_DIR, TRANSCRIPTS_DIR, STATEMENTS_DIR):
        if not directory.exists():
            continue
        for pdf_path in directory.glob("*.pdf"):
            meeting_date = extract_date_from_filename(pdf_path.name)
            if meeting_date:
                dates.add(meeting_date)
    return sorted(dates)


def statement_date_candidates(meeting_date):
    """Return likely statement release dates for a meeting date."""
    date_obj = datetime.strptime(meeting_date, "%Y-%m-%d").date()
    candidates = [
        date_obj,
        date_obj + timedelta(days=1),
        date_obj - timedelta(days=1),
    ]
    return [candidate.isoformat() for candidate in candidates]


def should_keep_statement_paragraph(text, css_class):
    """Return whether a press-release paragraph is part of the statement body."""
    if css_class in {"article__time", "releaseTime"}:
        return False
    if text.startswith("For media inquiries"):
        return False
    if "Implementation Note issued" in text:
        return False
    if text in {"Share"}:
        return False
    return True


def extract_statement_text(html, url):
    """Parse statement HTML and return statement body text."""
    parser = StatementHTMLParser()
    parser.feed(html)

    paragraphs = [
        text
        for text, css_class in parser.paragraphs
        if should_keep_statement_paragraph(text, css_class)
    ]
    if not paragraphs:
        raise ValueError(f"No statement body paragraphs found at {url}")

    return " ".join(paragraphs)


def fetch_statement_count(session, meeting_date):
    """Fetch a statement page and return its AI count and source URL."""
    last_error = None
    for candidate_date in statement_date_candidates(meeting_date):
        url = STATEMENT_URL.format(date=compact_date(candidate_date))
        try:
            response = session.get(url, headers=REQUEST_HEADERS, timeout=(5, 15))
            if response.status_code == 404:
                last_error = ValueError(f"Statement not found at {url}")
                continue
            response.raise_for_status()
            return count_ai_references(extract_statement_text(response.text, url)), url
        except requests.RequestException as exc:
            last_error = exc

    raise last_error or ValueError(f"No statement found for {meeting_date}")


def fetch_statement_row(meeting_date):
    """Fetch one statement AI-count row."""
    with requests.Session() as session:
        count, source = fetch_statement_count(session, meeting_date)
    return {
        "meeting_date": meeting_date,
        "document_type": "statement",
        "ai_references": count,
        "source": source,
    }


def count_pdf_ai_references(pdf_path):
    """Extract PDF text and count AI references."""
    total = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            total += count_ai_references(page.extract_text() or "")
    return total


def build_pdf_rows(directory, document_type):
    """Build AI-count rows for cached PDFs in a directory."""
    rows = []
    pdf_paths = sorted(directory.glob("*.pdf"))
    for idx, pdf_path in enumerate(pdf_paths, start=1):
        meeting_date = extract_date_from_filename(pdf_path.name)
        if not meeting_date:
            continue
        print(
            f"  {document_type.title()} {idx}/{len(pdf_paths)}: {meeting_date}",
            flush=True,
        )
        rows.append({
            "meeting_date": meeting_date,
            "document_type": document_type,
            "ai_references": count_pdf_ai_references(pdf_path),
            "source": str(pdf_path.relative_to(BASE_DIR)),
        })
    return rows


def build_statement_rows():
    """Build AI-count rows for FOMC statements."""
    meeting_dates = load_dates_from_pdf_dirs()
    rows = []
    print(f"  Fetching {len(meeting_dates)} statements...", flush=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_statement_row, meeting_date): meeting_date
            for meeting_date in meeting_dates
        }
        completed = 0
        for future in as_completed(futures):
            completed += 1
            meeting_date = futures[future]
            try:
                rows.append(future.result())
                print(
                    f"  Statement {completed}/{len(meeting_dates)}: {meeting_date}",
                    flush=True,
                )
            except (requests.RequestException, ValueError) as exc:
                print(f"  Skipped statement {meeting_date}: {exc}", flush=True)
    return rows


def build_rows():
    """Build AI mention rows for minutes, press conferences, and statements."""
    rows = []
    rows.extend(build_pdf_rows(MINUTES_DIR, "minutes"))
    rows.extend(build_pdf_rows(TRANSCRIPTS_DIR, "press_conference"))
    rows.extend(build_statement_rows())
    return sorted(rows, key=lambda row: (row["meeting_date"], row["document_type"]))


def write_rows(rows):
    """Write AI mention rows to CSV."""
    OUTPUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DATA, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["meeting_date", "document_type", "ai_references", "source"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_stacked_bars(rows):
    """Create stacked column chart of AI references by document type."""
    dates = sorted({row["meeting_date"] for row in rows})
    data = defaultdict(lambda: {
        "minutes": 0,
        "press_conference": 0,
        "statement": 0,
    })

    for row in rows:
        data[row["meeting_date"]][row["document_type"]] = int(row["ai_references"])

    date_values = [datetime.strptime(date, "%Y-%m-%d").date() for date in dates]
    minutes = [data[date]["minutes"] for date in dates]
    press_conferences = [data[date]["press_conference"] for date in dates]
    statements = [data[date]["statement"] for date in dates]
    press_bottom = minutes
    statement_bottom = [
        minute + press
        for minute, press in zip(minutes, press_conferences)
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.bar(date_values, minutes, width=28, color="#4e79a7", label="Minutes")
    ax.bar(
        date_values,
        press_conferences,
        width=28,
        bottom=press_bottom,
        color="#f28e2b",
        label="Press Conference",
    )
    ax.bar(
        date_values,
        statements,
        width=28,
        bottom=statement_bottom,
        color="#59a14f",
        label="Statement",
    )

    ax.set_title(
        "FOMC References to AI or Artificial Intelligence",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("FOMC Meeting Date")
    ax.set_ylabel("References")
    max_total = max(
        minute + press + statement
        for minute, press, statement in zip(minutes, press_conferences, statements)
    )
    ax.set_ylim(0, max(1, max_total) * 1.15)
    ax.xaxis.set_major_locator(YearLocator(base=1))
    ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    """Compute AI mentions and produce a stacked column chart."""
    print("Computing FOMC AI references...")
    rows = build_rows()
    write_rows(rows)
    plot_stacked_bars(rows)

    totals = defaultdict(int)
    for row in rows:
        totals[row["document_type"]] += int(row["ai_references"])

    print(f"Saved data: {OUTPUT_DATA}")
    print(f"Saved chart: {OUTPUT_PLOT}")
    print(
        "Totals: "
        f"{totals['minutes']} minutes, "
        f"{totals['press_conference']} press conference, "
        f"{totals['statement']} statement"
    )


if __name__ == "__main__":
    main()
