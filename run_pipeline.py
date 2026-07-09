#!/usr/bin/env python3
"""
FOMC Document Analysis Pipeline

This script runs the complete analysis pipeline:
1. Downloads FOMC statements, press conference transcripts, and minutes
2. Extracts word counts for 'immigration' and 'productivity'
3. Creates a visualization of trends over time

Usage:
    python run_pipeline.py
    python run_pipeline.py --incremental
    python run_pipeline.py --incremental --skip-viz-if-no-changes
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the FOMC document analysis pipeline.")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only extract missing word-count rows from existing PDFs.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading PDFs.",
    )
    parser.add_argument(
        "--skip-viz",
        action="store_true",
        help="Skip visualization generation.",
    )
    parser.add_argument(
        "--skip-viz-if-no-changes",
        action="store_true",
        help="In incremental mode, skip visualization when no PDFs were processed.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("FOMC Document Analysis Pipeline")
    print("=" * 60)
    print()

    processed_pdfs = 0

    # Step 1: Download documents
    if args.skip_download:
        print("STEP 1: Downloading FOMC documents")
        print("-" * 60)
        print("Skipped (--skip-download)")
        print()
    else:
        print("STEP 1: Downloading FOMC documents")
        print("-" * 60)
        from download_documents import download_all_documents

        download_all_documents()
        print()

    # Step 2: Extract word counts
    print("STEP 2: Extracting word counts")
    print("-" * 60)
    from extract_word_counts import extract_all_word_counts

    processed_pdfs = extract_all_word_counts(incremental=args.incremental)
    print()

    # Step 3: Create visualization
    skip_viz = args.skip_viz
    if (
        not skip_viz
        and args.skip_viz_if_no_changes
        and args.incremental
        and processed_pdfs == 0
    ):
        skip_viz = True

    if skip_viz:
        print("STEP 3: Creating visualization")
        print("-" * 60)
        if args.skip_viz:
            print("Skipped (--skip-viz)")
        else:
            print("Skipped (--skip-viz-if-no-changes and no PDFs were processed)")
        print()
    else:
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
    print("  - data/statements/      : FOMC statements (PDF)")
    print("  - data/transcripts/     : FOMC press conference transcripts (PDF)")
    print("  - data/minutes/         : FOMC meeting minutes (PDF)")
    print("  - data/word_counts.csv  : Word count analysis results")
    print("  - output/               : Visualization charts (PNG)")
    print("=" * 60)


if __name__ == "__main__":
    main()
