# GDELT Text Extraction API

Welcome to the GDELT Text Extraction API project! This API is designed to facilitate the extraction of formatted JSON text from GDELT, providing a streamlined interface for data collection and analysis of news articles.

## Features

- **Streamlined Interface:** Adjust your search by tone, language, keywords, repetitions, and more.
- **Search Saving:** Save your searches and found links for easy future access.
- **JSON Extraction:** Extract text related to GDELT links in JSON format for advanced analysis.
- **Simple Automation:** Easily run automated scripts to extract information on specific domains.

## Installation

*Instructions for installation will go here.*

## Usage

You can use the dashboard by running the following command:

```bash
streamlit run DataGatheringDashboard.py
```

If you are a programmer and interested in automatic data scraping, modify AutoScraper.py with your customized filters and run:

```bash
python DataGatheringDashboard.py
```

## Acknowledgments

*This project includes code from the following repository: [(https://github.com/alex9smith/gdelt-doc-api)].*


## Future Updates

Parallelization of text extraction from links retrived by GDELT API