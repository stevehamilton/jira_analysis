# Jira Metrics Analysis Script

## Overview
This Python script analyzes Jira project metrics by processing CSV exports from Jira queries. It generates visualizations and statistical analysis for story points, cycle time, and story counts across different projects. The script creates both time-series plots and histograms for each project, helping teams understand their project metrics and identify patterns or changes over time.

## Prerequisites
- Python 3.x
- Required Python packages:
  - pandas
  - matplotlib
  - numpy

## Setup
1. Create a directory called `raw_data` in the same folder as the script
2. Export your Jira data as CSV files:
   - Use shared queries in Jira to export the data
   - Note: Jira limits exports to 1,000 rows at a time
   - Place all exported CSV files in the `raw_data` folder
   - The script will automatically combine all CSV files in the directory

## Required CSV Fields
The script expects the following columns in your Jira CSV exports:
- Updated
- Created
- Resolved
- Summary
- Project name
- Custom field (Story Points)
- Description

## Output
The script generates several outputs for each project:

### Visualizations
1. Time-series plots (`{project}-Timeseries.png`):
   - Bi-weekly Story Points with standard deviation
   - Bi-weekly Mean Cycle Time with standard deviation changes
   - Bi-weekly Story Count with standard deviation changes

2. Histogram plots (`{project}-Hist.png`):
   - Story Point distribution
   - Cycle Time distribution
   - Description Length distribution

### Data Summary
A `summary_data.txt` file containing:
- Statistical descriptions of metrics for each project
- Description length analysis

## How It Works
1. Combines all CSV files from the `raw_data` directory
2. Calculates cycle time for each issue
   - Note: Uses a simplified cycle time calculation based on resolution date and creation date
3. Groups data into bi-weekly intervals
4. Calculates rolling statistics and standard deviations
5. Generates visualizations and summary statistics for each project

## Notes
- The cycle time calculation is simplified and may not reflect the exact workflow in all cases
- For projects that don't set the 'Resolved' field, the script uses the 'Updated' field as a fallback
- Story points default to 0 if not set
- The script automatically handles missing or null values in the data

## Usage
1. Place your Jira CSV exports in the `raw_data` folder
2. Run the script:
```bash
python jira_metrics.py
```
3. Check the output directory for generated plots and the summary data file

## Customization
You can modify the script to:
- Adjust the time window for grouping (currently set to 2 weeks)
- Change the plotting parameters
- Add additional metrics or visualizations
- Modify the cycle time calculation method

