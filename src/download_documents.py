#!/usr/bin/env python3
"""
Step 1: Download FOMC statements, press conference transcripts, and minutes PDFs.

Downloads documents from the Federal Reserve website for all FOMC meetings
from 2012-2026.
"""

import re
from pathlib import Path
import requests

# FOMC calendar page for dynamic date fetching
CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

# Fallback FOMC meeting dates (used if scraping fails)
FALLBACK_MEETING_DATES = [
    # 2012
    "20120125", "20120313", "20120425", "20120620", "20120801",
    "20120913", "20121023", "20121212",
    # 2013
    "20130130", "20130320", "20130501", "20130619", "20130731",
    "20130918", "20131030", "20131218",
    # 2014
    "20140129", "20140319", "20140430", "20140618", "20140730",
    "20140917", "20141029", "20141217",
    # 2015
    "20150128", "20150318", "20150429", "20150617", "20150729",
    "20150917", "20151028", "20151216",
    # 2016
    "20160127", "20160316", "20160427", "20160615", "20160727",
    "20160921", "20161102", "20161214",
    # 2017
    "20170201", "20170315", "20170503", "20170614", "20170726",
    "20170920", "20171101", "20171213",
    # 2018
    "20180131", "20180321", "20180502", "20180613", "20180801",
    "20180926", "20181108", "20181219",
    # 2019
    "20190130", "20190320", "20190501", "20190619", "20190731",
    "20190918", "20191030", "20191211",
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
    # 2026
    "20260128", "20260318", "20260429", "20260617",
]

# URL templates
STATEMENT_URL = "https://www.federalreserve.gov/monetarypolicy/files/monetary{date}a1.pdf"
TRANSCRIPT_URL = "https://www.federalreserve.gov/mediacenter/files/FOMCpresconf{date}.pdf"
MINUTES_URL = "https://www.federalreserve.gov/monetarypolicy/files/fomcminutes{date}.pdf"

# Output directories (relative to project root, not src/)
BASE_DIR = Path(__file__).parent.parent
STATEMENTS_DIR = BASE_DIR / "data" / "statements"
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
MINUTES_DIR = BASE_DIR / "data" / "minutes"


def fetch_meeting_dates():
    """Fetch FOMC meeting dates, combining fallback dates with scraped dates."""
    # Start with fallback dates (ensures historical coverage)
    all_dates = set(FALLBACK_MEETING_DATES)

    try:
        response = requests.get(CALENDAR_URL, timeout=30)
        response.raise_for_status()

        # Extract dates from document links
        date_pattern = r'fomcminutes(\d{8})\.pdf'
        scraped = set(re.findall(date_pattern, response.text))

        # Check statement links
        statement_pattern = r'monetary(\d{8})a1\.pdf'
        scraped.update(re.findall(statement_pattern, response.text))

        # Also check transcript links for very recent meetings
        transcript_pattern = r'FOMCpresconf(\d{8})\.pdf'
        scraped.update(re.findall(transcript_pattern, response.text))

        # Check press conference page links (handles both fomcpresconf and fomcpressconf)
        pressconf_pattern = r'fomcpress?conf(\d{8})\.htm'
        scraped.update(re.findall(pressconf_pattern, response.text))

        if scraped:
            new_dates = scraped - all_dates
            if new_dates:
                print(f"Found {len(new_dates)} new meeting dates: {sorted(new_dates)}")
            all_dates.update(scraped)
    except Exception as e:
        print(f"Warning: Could not fetch calendar ({e}), using fallback dates only")

    return sorted(all_dates)


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
    """Download all FOMC statements, transcripts, and minutes."""
    # Create directories
    STATEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    MINUTES_DIR.mkdir(parents=True, exist_ok=True)
    meeting_dates = fetch_meeting_dates()

    statement_count = 0
    transcript_count = 0
    minutes_count = 0
    failed_statements = []
    failed_transcripts = []
    failed_minutes = []

    print("Downloading FOMC documents...")
    print("=" * 50)

    for date in meeting_dates:
        # Download statement
        statement_url = STATEMENT_URL.format(date=date)
        statement_path = STATEMENTS_DIR / f"monetary{date}a1.pdf"

        if statement_path.exists():
            print(f"[{date}] Statement already exists, skipping")
        else:
            print(f"[{date}] Downloading statement...", end=" ")
            if download_file(statement_url, statement_path):
                print("OK")
                statement_count += 1
            else:
                print("FAILED")
                failed_statements.append(date)

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
    print(f"  Statements: {statement_count} new downloads")
    print(f"  Transcripts: {transcript_count} new downloads")
    print(f"  Minutes: {minutes_count} new downloads")

    if failed_statements:
        print(f"\n  Failed statements: {failed_statements}")
    if failed_transcripts:
        print(f"\n  Failed transcripts: {failed_transcripts}")
    if failed_minutes:
        print(f"  Failed minutes: {failed_minutes}")
        print("  Note: March 3, 2020 was an emergency meeting with no published minutes.")

    total_statements = len(list(STATEMENTS_DIR.glob("*.pdf")))
    total_transcripts = len(list(TRANSCRIPTS_DIR.glob("*.pdf")))
    total_minutes = len(list(MINUTES_DIR.glob("*.pdf")))
    print(f"\n  Total statements on disk: {total_statements}")
    print(f"  Total transcripts on disk: {total_transcripts}")
    print(f"  Total minutes on disk: {total_minutes}")


if __name__ == "__main__":
    download_all_documents()
