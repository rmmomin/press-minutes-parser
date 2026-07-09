# FOMC Immigration & Productivity Trends

An end-to-end pipeline to scrape FOMC (Federal Open Market Committee) statements, meeting minutes, and press conference transcripts, then analyze trends in references to "immigration" and "productivity".

## Overview

This project downloads official Federal Reserve documents and tracks how often the Fed discusses immigration and productivity over time. The analysis covers all FOMC meetings from 2012 through June 2026.

## Pipeline Steps

1. **Download Documents** - Scrapes statement, press conference transcript, and meeting minutes PDFs from federalreserve.gov
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

Run a fast incremental update (process only missing counts):

```bash
python run_pipeline.py --incremental
```

Run incremental update and skip chart regeneration when nothing changed:

```bash
python run_pipeline.py --incremental --skip-viz-if-no-changes
```

Or run individual steps:

```bash
python src/download_documents.py    # Step 1: Download PDFs
python src/extract_word_counts.py   # Step 2: Extract word counts
python src/create_visualization.py  # Step 3: Generate charts
```

Run extraction-only incremental mode:

```bash
python src/extract_word_counts.py --incremental
```

Generate the quarterly productivity mentions vs labor productivity chart:

```bash
python src/plot_productivity_vs_labor_yoy.py
```

Generate the FOMC minutes and statement length column charts:

```bash
python src/plot_document_lengths.py
```

## Output

### Data Files
- `data/statements/` - Cached FOMC statement PDFs where available (1 file)
- `data/transcripts/` - FOMC press conference transcript PDFs (88 files)
- `data/minutes/` - FOMC meeting minutes PDFs (116 files)
- `data/word_counts.csv` - Extracted word counts
- `data/document_lengths.csv` - FOMC minutes and statement lengths by meeting (116 minutes rows, 117 statement rows)
- `data/productivity_mentions_vs_labor_productivity_yoy_quarterly.csv` - Quarterly productivity mentions joined to labor productivity y/y %

### Visualizations
- `output/fomc_word_trends.png` - Combined bar + line chart
- `output/fomc_word_trends_bars.png` - Grouped stacked bar chart
- `output/fomc_word_trends_lines.png` - Trend lines chart
- `output/fomc_minutes_lengths.png` - Column chart of FOMC minutes length by meeting
- `output/fomc_statement_lengths.png` - Column chart of FOMC statement length by meeting
- `output/productivity_mentions_vs_labor_productivity_yoy_quarterly.png` - Quarterly productivity mentions vs labor productivity y/y %

## Data Source

Documents are downloaded from the [Federal Reserve FOMC Calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) and the Federal Reserve historical FOMC pages.

## Project Structure

```
press-minutes-parser/
├── README.md
├── requirements.txt
├── run_pipeline.py          # Main entry point
├── src/
│   ├── download_documents.py
│   ├── extract_word_counts.py
│   ├── create_visualization.py
│   ├── plot_document_lengths.py
│   └── plot_productivity_vs_labor_yoy.py
├── data/
│   ├── statements/          # Downloaded PDFs
│   ├── transcripts/         # Downloaded PDFs
│   ├── minutes/             # Downloaded PDFs
│   ├── word_counts.csv      # Analysis results
│   ├── document_lengths.csv # Document length results
│   └── productivity_mentions_vs_labor_productivity_yoy_quarterly.csv
└── output/
    ├── fomc_word_trends*.png
    ├── fomc_*_lengths.png
    └── productivity_mentions_vs_labor_productivity_yoy_quarterly.png
```

## Key Findings

- Coverage includes 117 FOMC meeting dates from `2012-01-25` through `2026-06-17`; press conference transcripts cover the subset of meetings where transcripts were published.
- Total mentions across all meetings:
  - `productivity`: `341` (`1` in statements, `180` in press conferences, `160` in minutes)
  - `immigration`: `95` (`0` in statements, `43` in press conferences, `52` in minutes)
- Productivity mentions remain persistent over the full sample, with the highest quarterly total in `2025-Q4` (`20` mentions).
- `2026-Q2` currently shows `15` productivity mentions from the April 29 and June 17, 2026 materials in the corpus.
- In the quarterly FRED comparison chart, labor productivity y/y data is available through `2026-Q1` (`2.7972%`); the `2026-Q2` mention bar is shown with a missing y/y value until FRED publishes that quarter.
