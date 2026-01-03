#!/usr/bin/env python3
"""
Step 1: Download FOMC press conference transcripts and minutes PDFs.

Downloads documents from the Federal Reserve website for all FOMC meetings
from 2020-2025.
"""

import os
from pathlib import Path
import requests

# All FOMC meeting dates from 2020-2025 (YYYYMMDD format)
MEETING_DATES = [
    # 2020
    "20200129", "20200303", "20200315", "20200429", "20200610",
    "20200729", "20200916", "20201105", "20201216",
    # 2021
    "20210127", "20210317", "20210428", "20210616", "20210728",
    "20210922", "20211103", "20211215",
    # 2022
    "20220126", "20220316", "20220504", "20220615", "20220727",
    "20220921", "20221102", "20221214",
    # 2023
    "20230201", "20230322", "20230503", "20230614", "20230726",
    "20230920", "20231101", "20231213",
    # 2024
    "20240131", "20240320", "20240501", "20240612", "20240731",
    "20240918", "20241107", "20241218",
    # 2025
    "20250129", "20250319", "20250507", "20250618", "20250730",
    "20250917", "20251029", "20251210",
]

# URL templates
TRANSCRIPT_URL = "https://www.federalreserve.gov/mediacenter/files/FOMCpresconf{date}.pdf"
MINUTES_URL = "https://www.federalreserve.gov/monetarypolicy/files/fomcminutes{date}.pdf"

# Output directories (relative to project root, not src/)
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
MINUTES_DIR = BASE_DIR / "data" / "minutes"


def download_file(url, output_path):
    """Download a file from URL to output path. Returns True if successful."""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
    except requests.RequestException as e:
        print(f"  Error downloading {url}: {e}")
        return False


def download_all_documents():
    """Download all FOMC transcripts and minutes."""
    # Create directories
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    MINUTES_DIR.mkdir(parents=True, exist_ok=True)

    transcript_count = 0
    minutes_count = 0
    failed_transcripts = []
    failed_minutes = []

    print("Downloading FOMC documents...")
    print("=" * 50)

    for date in MEETING_DATES:
        # Download transcript
        transcript_url = TRANSCRIPT_URL.format(date=date)
        transcript_path = TRANSCRIPTS_DIR / f"FOMCpresconf{date}.pdf"

        if transcript_path.exists():
            print(f"[{date}] Transcript already exists, skipping")
        else:
            print(f"[{date}] Downloading transcript...", end=" ")
            if download_file(transcript_url, transcript_path):
                print("OK")
                transcript_count += 1
            else:
                print("FAILED")
                failed_transcripts.append(date)

        # Download minutes
        minutes_url = MINUTES_URL.format(date=date)
        minutes_path = MINUTES_DIR / f"fomcminutes{date}.pdf"

        if minutes_path.exists():
            print(f"[{date}] Minutes already exists, skipping")
        else:
            print(f"[{date}] Downloading minutes...", end=" ")
            if download_file(minutes_url, minutes_path):
                print("OK")
                minutes_count += 1
            else:
                print("FAILED")
                failed_minutes.append(date)

    # Summary
    print("\n" + "=" * 50)
    print("Download Summary:")
    print(f"  Transcripts: {transcript_count} new downloads")
    print(f"  Minutes: {minutes_count} new downloads")

    if failed_transcripts:
        print(f"\n  Failed transcripts: {failed_transcripts}")
    if failed_minutes:
        print(f"  Failed minutes: {failed_minutes}")
        print("  Note: March 3, 2020 was an emergency meeting with no published minutes.")

    total_transcripts = len(list(TRANSCRIPTS_DIR.glob("*.pdf")))
    total_minutes = len(list(MINUTES_DIR.glob("*.pdf")))
    print(f"\n  Total transcripts on disk: {total_transcripts}")
    print(f"  Total minutes on disk: {total_minutes}")


if __name__ == "__main__":
    download_all_documents()
