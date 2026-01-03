#!/usr/bin/env python3
"""
FOMC Document Analysis Pipeline

This script runs the complete analysis pipeline:
1. Downloads FOMC press conference transcripts and minutes
2. Extracts word counts for 'immigration' and 'productivity'
3. Creates a visualization of trends over time

Usage:
    python run_pipeline.py
"""

import sys
from pathlib import Path

# Add the src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    print("=" * 60)
    print("FOMC Document Analysis Pipeline")
    print("=" * 60)
    print()

    # Step 1: Download documents
    print("STEP 1: Downloading FOMC documents")
    print("-" * 60)
    from download_documents import download_all_documents
    download_all_documents()
    print()

    # Step 2: Extract word counts
    print("STEP 2: Extracting word counts")
    print("-" * 60)
    from extract_word_counts import extract_all_word_counts
    extract_all_word_counts()
    print()

    # Step 3: Create visualization
    print("STEP 3: Creating visualization")
    print("-" * 60)
    from create_visualization import create_visualization
    create_visualization()
    print()

    # Done
    print("=" * 60)
    print("Pipeline complete!")
    print()
    print("Output files:")
    print("  - data/transcripts/     : FOMC press conference transcripts (PDF)")
    print("  - data/minutes/         : FOMC meeting minutes (PDF)")
    print("  - data/word_counts.csv  : Word count analysis results")
    print("  - output/               : Visualization charts (PNG)")
    print("=" * 60)


if __name__ == "__main__":
    main()
