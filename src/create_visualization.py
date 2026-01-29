#!/usr/bin/env python3
"""
Step 3: Create visualization of FOMC word mention trends.

Generates three output files:
1. fomc_word_trends.png - Combined bar + line chart
2. fomc_word_trends_bars.png - Bar chart only
3. fomc_word_trends_lines.png - Line chart only
"""

import csv
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Paths (relative to project root, not src/)
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "data" / "word_counts.csv"
OUTPUT_DIR = BASE_DIR / "output"


def load_data():
    """Load and organize word count data from CSV."""
    data = defaultdict(lambda: {
        'immigration_transcript': 0,
        'immigration_minutes': 0,
        'productivity_transcript': 0,
        'productivity_minutes': 0,
    })

    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['meeting_date']
            key = f"{row['word']}_{row['document_type']}"
            data[date][key] = int(row['count'])

    sorted_dates = sorted(data.keys())

    return {
        'dates': sorted_dates,
        'immigration_transcript': [data[d]['immigration_transcript'] for d in sorted_dates],
        'immigration_minutes': [data[d]['immigration_minutes'] for d in sorted_dates],
        'productivity_transcript': [data[d]['productivity_transcript'] for d in sorted_dates],
        'productivity_minutes': [data[d]['productivity_minutes'] for d in sorted_dates],
    }


FOOTNOTE = "Note: As of January 29, 2026, FOMC minutes for the January 27-28, 2026 meeting are not yet available."


def draw_bar_chart(ax, data):
    """Draw grouped stacked bar chart on given axes."""
    sorted_dates = data['dates']
    immigration_transcript = data['immigration_transcript']
    immigration_minutes = data['immigration_minutes']
    productivity_transcript = data['productivity_transcript']
    productivity_minutes = data['productivity_minutes']

    # Colors
    colors = {
        'immigration_transcript': '#1f77b4',  # Dark blue
        'immigration_minutes': '#aec7e8',     # Light blue
        'productivity_transcript': '#ff7f0e', # Dark orange
        'productivity_minutes': '#ffbb78',    # Light orange
    }

    # Bar positions
    x = list(range(len(sorted_dates)))
    width = 0.35

    # Immigration bars (left)
    x_imm = [i - width/2 for i in x]
    ax.bar(x_imm, immigration_transcript, width, label='Immigration Transcript',
           color=colors['immigration_transcript'])
    ax.bar(x_imm, immigration_minutes, width, bottom=immigration_transcript,
           label='Immigration Minutes', color=colors['immigration_minutes'])

    # Productivity bars (right)
    x_prod = [i + width/2 for i in x]
    ax.bar(x_prod, productivity_transcript, width, label='Productivity Transcript',
           color=colors['productivity_transcript'])
    ax.bar(x_prod, productivity_minutes, width, bottom=productivity_transcript,
           label='Productivity Minutes', color=colors['productivity_minutes'])

    # Format
    date_labels = [d[:7] for d in sorted_dates]
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=7)
    ax.set_xlabel('FOMC Meeting Date', fontsize=10)
    ax.set_ylabel('Word Count', fontsize=10)
    ax.set_title('FOMC Documents: Immigration and Productivity Mentions (Stacked Bars)',
                 fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)


def draw_line_chart(ax, data):
    """Draw line chart showing totals on given axes."""
    sorted_dates = data['dates']

    # Calculate totals
    immigration_total = [t + m for t, m in zip(data['immigration_transcript'], data['immigration_minutes'])]
    productivity_total = [t + m for t, m in zip(data['productivity_transcript'], data['productivity_minutes'])]

    x = list(range(len(sorted_dates)))

    # Plot lines
    ax.plot(x, immigration_total, color='#1f77b4', linewidth=2, marker='o', markersize=4,
            label='Immigration Total')
    ax.plot(x, productivity_total, color='#ff7f0e', linewidth=2, marker='s', markersize=4,
            label='Productivity Total')

    # Format
    date_labels = [d[:7] for d in sorted_dates]
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=7)
    ax.set_xlabel('FOMC Meeting Date', fontsize=10)
    ax.set_ylabel('Total Mentions', fontsize=10)
    ax.set_title('FOMC Documents: Immigration and Productivity Mention Trends',
                 fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)


def create_visualization():
    """Create all three visualization outputs."""

    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} does not exist. Run extract_word_counts.py first.")
        return

    print("Creating visualizations...")
    print("=" * 50)

    # Load data
    data = load_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Combined chart (bar + line)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12))
    draw_bar_chart(ax1, data)
    draw_line_chart(ax2, data)
    fig.text(0.5, 0.01, FOOTNOTE, ha='center', fontsize=9, style='italic')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    combined_path = OUTPUT_DIR / "fomc_word_trends.png"
    plt.savefig(combined_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {combined_path}")

    # 2. Bar chart only
    fig, ax = plt.subplots(figsize=(18, 8))
    draw_bar_chart(ax, data)
    fig.text(0.5, 0.01, FOOTNOTE, ha='center', fontsize=9, style='italic')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    bars_path = OUTPUT_DIR / "fomc_word_trends_bars.png"
    plt.savefig(bars_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {bars_path}")

    # 3. Line chart only
    fig, ax = plt.subplots(figsize=(18, 6))
    draw_line_chart(ax, data)
    fig.text(0.5, 0.01, FOOTNOTE, ha='center', fontsize=9, style='italic')
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    lines_path = OUTPUT_DIR / "fomc_word_trends_lines.png"
    plt.savefig(lines_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {lines_path}")

    # Summary
    print("\n" + "=" * 50)
    print("Data summary:")
    print(f"  Meeting dates: {len(data['dates'])}")
    print(f"  Date range: {data['dates'][0]} to {data['dates'][-1]}")
    print(f"  Immigration Transcript: {sum(data['immigration_transcript'])}")
    print(f"  Immigration Minutes: {sum(data['immigration_minutes'])}")
    print(f"  Productivity Transcript: {sum(data['productivity_transcript'])}")
    print(f"  Productivity Minutes: {sum(data['productivity_minutes'])}")


if __name__ == "__main__":
    create_visualization()
