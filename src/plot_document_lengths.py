#!/usr/bin/env python3
"""
Compute and plot FOMC document lengths.

Minutes are measured from cached PDFs in data/minutes/. Statements are measured
from Federal Reserve statement HTML pages for the same meeting dates covered by
the local minutes/transcript PDF cache.
"""

import csv
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
OUTPUT_DATA = BASE_DIR / "data" / "document_lengths.csv"
MINUTES_PLOT = OUTPUT_DIR / "fomc_minutes_lengths.png"
STATEMENTS_PLOT = OUTPUT_DIR / "fomc_statement_lengths.png"

STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary{date}a.htm"
REQUEST_HEADERS = {
    "User-Agent": "press-minutes-parser/1.0 (+https://www.federalreserve.gov/)",
}
WORD_PATTERN = re.compile(r"\b[\w'-]+\b")


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


def count_words(text):
    """Count word-like tokens in text."""
    return len(WORD_PATTERN.findall(text))


def extract_date_from_filename(filename):
    """Extract date from filename like fomcminutes20200129.pdf -> 2020-01-29."""
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


def count_words_in_pdf(pdf_path):
    """Extract PDF text and count word-like tokens."""
    total = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            total += count_words(page.extract_text() or "")
    return total


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


def parse_statement_html(html, url):
    """Parse statement HTML and return its word count."""
    parser = StatementHTMLParser()
    parser.feed(html)

    paragraphs = [
        text
        for text, css_class in parser.paragraphs
        if should_keep_statement_paragraph(text, css_class)
    ]
    if not paragraphs:
        raise ValueError(f"No statement body paragraphs found at {url}")

    return count_words(" ".join(paragraphs))


def fetch_statement_length(session, meeting_date):
    """Fetch a statement HTML page and return its word count, URL, and release date."""
    last_error = None
    for candidate_date in statement_date_candidates(meeting_date):
        url = STATEMENT_URL.format(date=compact_date(candidate_date))
        try:
            response = session.get(url, headers=REQUEST_HEADERS, timeout=(5, 15))
            if response.status_code == 404:
                last_error = ValueError(f"Statement not found at {url}")
                continue
            response.raise_for_status()
            return parse_statement_html(response.text, url), url, candidate_date
        except requests.RequestException as exc:
            last_error = exc

    raise last_error or ValueError(f"No statement found for {meeting_date}")


def fetch_statement_row(meeting_date):
    """Fetch one statement length row."""
    with requests.Session() as session:
        length_words, source, statement_date = fetch_statement_length(session, meeting_date)
    return {
        "meeting_date": statement_date,
        "document_type": "statement",
        "length_words": length_words,
        "source": source,
    }


def build_length_rows():
    """Build document length rows for minutes and statements."""
    rows = []

    minutes_paths = sorted(MINUTES_DIR.glob("*.pdf"))
    for idx, pdf_path in enumerate(minutes_paths, start=1):
        meeting_date = extract_date_from_filename(pdf_path.name)
        if not meeting_date:
            continue
        print(f"  Minutes {idx}/{len(minutes_paths)}: {meeting_date}", flush=True)
        rows.append({
            "meeting_date": meeting_date,
            "document_type": "minutes",
            "length_words": count_words_in_pdf(pdf_path),
            "source": str(pdf_path.relative_to(BASE_DIR)),
        })

    statement_dates = load_dates_from_pdf_dirs()
    print(f"  Fetching {len(statement_dates)} statements...", flush=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_statement_row, meeting_date): meeting_date
            for meeting_date in statement_dates
        }
        completed = 0
        for future in as_completed(futures):
            completed += 1
            meeting_date = futures[future]
            try:
                rows.append(future.result())
                print(
                    f"  Statement {completed}/{len(statement_dates)}: {meeting_date}",
                    flush=True,
                )
            except (requests.RequestException, ValueError) as exc:
                print(f"  Skipped statement {meeting_date}: {exc}", flush=True)

    return sorted(rows, key=lambda row: (row["meeting_date"], row["document_type"]))


def write_rows(rows):
    """Write document lengths to CSV."""
    OUTPUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DATA, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["meeting_date", "document_type", "length_words", "source"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_lengths(rows, document_type, output_path, title, color):
    """Create a column chart for a document type."""
    filtered = [row for row in rows if row["document_type"] == document_type]
    if not filtered:
        raise ValueError(f"No rows found for document type: {document_type}")

    dates = [
        datetime.strptime(row["meeting_date"], "%Y-%m-%d").date()
        for row in filtered
    ]
    lengths = [int(row["length_words"]) for row in filtered]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.bar(dates, lengths, width=28, color=color, alpha=0.85)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("FOMC Meeting Date")
    ax.set_ylabel("Length (words)")
    ax.xaxis.set_major_locator(YearLocator(base=1))
    ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    """Compute document lengths and produce column charts."""
    print("Computing FOMC document lengths...")
    rows = build_length_rows()
    write_rows(rows)

    plot_lengths(
        rows,
        "minutes",
        MINUTES_PLOT,
        "FOMC Minutes Length by Meeting",
        "#4e79a7",
    )
    plot_lengths(
        rows,
        "statement",
        STATEMENTS_PLOT,
        "FOMC Statement Length by Meeting",
        "#59a14f",
    )

    minutes_count = sum(1 for row in rows if row["document_type"] == "minutes")
    statements_count = sum(1 for row in rows if row["document_type"] == "statement")
    print(f"Saved data: {OUTPUT_DATA}")
    print(f"Saved minutes chart: {MINUTES_PLOT}")
    print(f"Saved statements chart: {STATEMENTS_PLOT}")
    print(f"Rows: {minutes_count} minutes, {statements_count} statements")


if __name__ == "__main__":
    main()
