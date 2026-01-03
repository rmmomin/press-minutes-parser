#!/usr/bin/env python3
"""
Step 2: Extract word counts from FOMC documents.

Processes all PDF files in data/transcripts/ and data/minutes/,
counting occurrences of specified words and outputting to CSV.
"""

import csv
import re
from pathlib import Path
import pdfplumber

# Words to count (case-insensitive)
WORDS_TO_COUNT = ['immigration', 'productivity']

# Directories (relative to project root, not src/)
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
MINUTES_DIR = BASE_DIR / "data" / "minutes"
OUTPUT_FILE = BASE_DIR / "data" / "word_counts.csv"


def extract_date_from_filename(filename):
    """Extract date from filename like FOMCpresconf20200129.pdf -> 2020-01-29"""
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None


def count_words_in_pdf(pdf_path, words):
    """Extract text from PDF and count occurrences of each word (case-insensitive)."""
    counts = {word: 0 for word in words}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ''
                text_lower = text.lower()
                for word in words:
                    # Use word boundaries for accurate counting
                    counts[word] += len(re.findall(r'\b' + word.lower() + r'\b', text_lower))
    except Exception as e:
        print(f"  Error processing {pdf_path}: {e}")
    return counts


def process_directory(directory, doc_type, words):
    """Process all PDFs in a directory and return results."""
    results = []
    pdf_files = sorted(directory.glob('*.pdf'))

    for pdf_path in pdf_files:
        meeting_date = extract_date_from_filename(pdf_path.name)
        if not meeting_date:
            print(f"  Could not parse date from: {pdf_path.name}")
            continue

        counts = count_words_in_pdf(pdf_path, words)

        for word, count in counts.items():
            results.append({
                'meeting_date': meeting_date,
                'document_type': doc_type,
                'word': word,
                'count': count
            })
        print(f"  Processed: {pdf_path.name}")

    return results


def extract_all_word_counts():
    """Process all documents and save word counts to CSV."""
    all_results = []

    print("Extracting word counts from FOMC documents...")
    print("=" * 50)

    # Check if directories exist
    if not TRANSCRIPTS_DIR.exists():
        print(f"Error: {TRANSCRIPTS_DIR} does not exist. Run download_documents.py first.")
        return
    if not MINUTES_DIR.exists():
        print(f"Error: {MINUTES_DIR} does not exist. Run download_documents.py first.")
        return

    print("\nProcessing transcripts...")
    all_results.extend(process_directory(TRANSCRIPTS_DIR, 'transcript', WORDS_TO_COUNT))

    print("\nProcessing minutes...")
    all_results.extend(process_directory(MINUTES_DIR, 'minutes', WORDS_TO_COUNT))

    # Sort by date, then document type, then word
    all_results.sort(key=lambda x: (x['meeting_date'], x['document_type'], x['word']))

    # Write to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['meeting_date', 'document_type', 'word', 'count'])
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 50)
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total records: {len(all_results)}")

    # Summary statistics
    from collections import defaultdict
    totals = defaultdict(lambda: defaultdict(int))
    for row in all_results:
        totals[row['word']][row['document_type']] += row['count']
        totals[row['word']]['total'] += row['count']

    print("\nSummary:")
    for word in WORDS_TO_COUNT:
        print(f"  {word}: {totals[word]['total']} total "
              f"({totals[word]['transcript']} in transcripts, "
              f"{totals[word]['minutes']} in minutes)")


if __name__ == "__main__":
    extract_all_word_counts()
