#!/usr/bin/env python3
"""
Step 2: Extract word counts from FOMC documents.

Processes PDF files in data/statements/, data/transcripts/, and data/minutes/,
counting occurrences of specified words and outputting to CSV.
"""

import argparse
import csv
from collections import defaultdict
import re
from pathlib import Path
import pdfplumber

# Words to count (case-insensitive)
WORDS_TO_COUNT = ["immigration", "productivity"]

# Precompile regex patterns for better performance
WORD_PATTERNS = {
    word: re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    for word in WORDS_TO_COUNT
}

# Directories (relative to project root, not src/)
BASE_DIR = Path(__file__).parent.parent
STATEMENTS_DIR = BASE_DIR / "data" / "statements"
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
MINUTES_DIR = BASE_DIR / "data" / "minutes"
OUTPUT_FILE = BASE_DIR / "data" / "word_counts.csv"


def extract_date_from_filename(filename):
    """Extract date from filename like FOMCpresconf20200129.pdf -> 2020-01-29"""
    match = re.search(r"(\d{8})", filename)
    if match:
        date_str = match.group(1)
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None


def load_existing_index(csv_path):
    """Load existing counts as an index keyed by (meeting_date, document_type, word)."""
    index = {}
    if not csv_path.exists():
        return index

    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            meeting_date = row.get("meeting_date")
            doc_type = row.get("document_type")
            word = row.get("word")

            if not meeting_date or not doc_type or not word:
                continue
            if word not in WORDS_TO_COUNT:
                continue

            try:
                count = int(row.get("count", 0))
            except (TypeError, ValueError):
                continue

            index[(meeting_date, doc_type, word)] = count

    return index


def count_words_in_pdf(pdf_path, words):
    """Extract text from PDF and count occurrences of each target word."""
    counts = {word: 0 for word in words}
    patterns = {word: WORD_PATTERNS[word] for word in words}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for word, pattern in patterns.items():
                    counts[word] += len(pattern.findall(text))
    except Exception as e:
        print(f"  Error processing {pdf_path}: {e}")

    return counts


def process_directory(directory, doc_type, index, expected_keys, incremental):
    """Process PDFs in a directory and update index with new counts."""
    processed_pdfs = 0
    pdf_files = sorted(directory.glob("*.pdf"))

    for pdf_path in pdf_files:
        meeting_date = extract_date_from_filename(pdf_path.name)
        if not meeting_date:
            print(f"  Could not parse date from: {pdf_path.name}")
            continue

        for word in WORDS_TO_COUNT:
            expected_keys.add((meeting_date, doc_type, word))

        missing_words = [
            word for word in WORDS_TO_COUNT
            if (meeting_date, doc_type, word) not in index
        ]

        if incremental and not missing_words:
            continue

        words_to_count = missing_words if incremental else WORDS_TO_COUNT
        counts = count_words_in_pdf(pdf_path, words_to_count)

        for word, count in counts.items():
            index[(meeting_date, doc_type, word)] = count

        processed_pdfs += 1
        if incremental:
            print(f"  Processed: {pdf_path.name} ({len(words_to_count)} missing words)")
        else:
            print(f"  Processed: {pdf_path.name}")

    return processed_pdfs


def build_results(index, expected_keys):
    """Build sorted result rows from index and expected keys."""
    results = []

    for meeting_date, doc_type, word in sorted(expected_keys):
        results.append(
            {
                "meeting_date": meeting_date,
                "document_type": doc_type,
                "word": word,
                "count": index.get((meeting_date, doc_type, word), 0),
            }
        )

    return results


def extract_all_word_counts(incremental: bool = False) -> int:
    """Process documents and save word counts to CSV.

    Args:
        incremental: If True, only parse PDFs with missing count rows.

    Returns:
        Number of PDFs processed in this run.
    """
    mode = "incremental" if incremental else "full"

    print("Extracting word counts from FOMC documents...")
    print(f"Mode: {mode}")
    print("=" * 50)

    # Check if directories exist
    if not TRANSCRIPTS_DIR.exists():
        print(f"Error: {TRANSCRIPTS_DIR} does not exist. Run download_documents.py first.")
        return 0
    if not MINUTES_DIR.exists():
        print(f"Error: {MINUTES_DIR} does not exist. Run download_documents.py first.")
        return 0

    index = load_existing_index(OUTPUT_FILE) if incremental else {}
    expected_keys = set()
    processed_pdfs = 0

    print("\nProcessing statements...")
    if STATEMENTS_DIR.exists():
        processed_pdfs += process_directory(
            STATEMENTS_DIR,
            "statement",
            index,
            expected_keys,
            incremental,
        )
    else:
        print(f"  Skipped: {STATEMENTS_DIR} does not exist")

    print("\nProcessing transcripts...")
    processed_pdfs += process_directory(
        TRANSCRIPTS_DIR,
        "transcript",
        index,
        expected_keys,
        incremental,
    )

    print("\nProcessing minutes...")
    processed_pdfs += process_directory(
        MINUTES_DIR,
        "minutes",
        index,
        expected_keys,
        incremental,
    )

    # Build sorted, deduped output rows
    all_results = build_results(index, expected_keys)

    # Write to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["meeting_date", "document_type", "word", "count"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 50)
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total records: {len(all_results)}")
    print(f"PDFs processed this run: {processed_pdfs}")

    # Summary statistics
    totals = defaultdict(lambda: defaultdict(int))
    for row in all_results:
        totals[row["word"]][row["document_type"]] += row["count"]
        totals[row["word"]]["total"] += row["count"]

    print("\nSummary:")
    for word in WORDS_TO_COUNT:
        print(
            f"  {word}: {totals[word]['total']} total "
            f"({totals[word]['statement']} in statements, "
            f"{totals[word]['transcript']} in transcripts, "
            f"{totals[word]['minutes']} in minutes)"
        )

    return processed_pdfs


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract FOMC word counts from PDFs.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--incremental",
        action="store_true",
        help="Only process PDFs missing count rows in data/word_counts.csv",
    )
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Force full rebuild of data/word_counts.csv",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    extract_all_word_counts(incremental=args.incremental)
