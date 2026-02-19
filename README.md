# FOMC Immigration & Productivity Trends

An end-to-end pipeline to scrape FOMC (Federal Open Market Committee) meeting minutes and press conference transcripts, then analyze trends in references to "immigration" and "productivity".

## Overview

This project downloads official Federal Reserve documents and tracks how often the Fed discusses immigration and productivity over time. The analysis covers all FOMC meetings from 2012 through January 2026.

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

Generate the quarterly productivity mentions vs labor productivity chart:

```bash
python src/plot_productivity_vs_labor_yoy.py
```

## Output

### Data Files
- `data/transcripts/` - FOMC press conference transcript PDFs (87 files)
- `data/minutes/` - FOMC meeting minutes PDFs (86 files)
- `data/word_counts.csv` - Extracted word counts
- `data/productivity_mentions_vs_labor_productivity_yoy_quarterly.csv` - Quarterly productivity mentions joined to labor productivity y/y %

### Visualizations
- `output/fomc_word_trends.png` - Combined bar + line chart
- `output/fomc_word_trends_bars.png` - Grouped stacked bar chart
- `output/fomc_word_trends_lines.png` - Trend lines chart
- `output/productivity_mentions_vs_labor_productivity_yoy_quarterly.png` - Quarterly productivity mentions vs labor productivity y/y %

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
│   ├── create_visualization.py
│   └── plot_productivity_vs_labor_yoy.py
├── data/
│   ├── transcripts/         # Downloaded PDFs
│   ├── minutes/             # Downloaded PDFs
│   ├── word_counts.csv      # Analysis results
│   └── productivity_mentions_vs_labor_productivity_yoy_quarterly.csv
└── output/
    ├── fomc_word_trends*.png
    └── productivity_mentions_vs_labor_productivity_yoy_quarterly.png
```

## Key Findings

- Coverage includes 87 FOMC meetings from `2012-01-25` through `2026-01-28`, including the January 28, 2026 minutes.
- Total mentions across all meetings:
  - `productivity`: `301` (`173` in press conferences, `128` in minutes)
  - `immigration`: `95` (`43` in press conferences, `52` in minutes)
- Productivity mentions remain persistent over the full sample, with the highest quarterly total in `2025-Q4` (`20` mentions).
- `2026-Q1` currently shows `14` productivity mentions (from the January 28, 2026 meeting).
- In the quarterly FRED comparison chart, labor productivity y/y data is available through `2025-Q3` (`1.9198%`); `2025-Q4` and `2026-Q1` mention bars are shown with missing y/y values until FRED publishes those quarters.
