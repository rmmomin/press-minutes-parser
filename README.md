# FOMC Immigration & Productivity Trends

An end-to-end pipeline to scrape FOMC (Federal Open Market Committee) meeting minutes and press conference transcripts, then analyze trends in references to "immigration" and "productivity".

## Overview

This project downloads official Federal Reserve documents and tracks how often the Fed discusses immigration and productivity over time. The analysis covers all FOMC meetings from 2012-2026.

## Pipeline Steps

1. **Download Documents** - Scrapes press conference transcripts and meeting minutes PDFs from federalreserve.gov
2. **Extract Word Counts** - Parses PDFs and counts occurrences of target words
3. **Visualize Trends** - Generates charts showing mention frequency over time

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- `pdfplumber` - PDF text extraction
- `matplotlib` - Chart generation
- `requests` - HTTP downloads

## Usage

Run the complete pipeline:

```bash
python run_pipeline.py
```

Or run individual steps:

```bash
python src/download_documents.py    # Step 1: Download PDFs
python src/extract_word_counts.py   # Step 2: Extract word counts
python src/create_visualization.py  # Step 3: Generate charts
```

## Output

### Data Files
- `data/transcripts/` - FOMC press conference transcript PDFs (87 files)
- `data/minutes/` - FOMC meeting minutes PDFs (85 files)
- `data/word_counts.csv` - Extracted word counts

### Visualizations
- `output/fomc_word_trends.png` - Combined bar + line chart
- `output/fomc_word_trends_bars.png` - Grouped stacked bar chart
- `output/fomc_word_trends_lines.png` - Trend lines chart

## Data Source

All documents are downloaded from the [Federal Reserve FOMC Calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm).

## Project Structure

```
press-minutes-parser/
├── README.md
├── requirements.txt
├── run_pipeline.py          # Main entry point
├── src/
│   ├── download_documents.py
│   ├── extract_word_counts.py
│   └── create_visualization.py
├── data/
│   ├── transcripts/         # Downloaded PDFs
│   ├── minutes/             # Downloaded PDFs
│   └── word_counts.csv      # Analysis results
└── output/
    └── *.png                # Generated charts
```

## Key Findings

The analysis shows that "productivity" has been a consistent topic in FOMC discussions since 2012, while "immigration" was rarely mentioned until late 2023, with a significant increase in discussion frequency throughout 2024-2025.
