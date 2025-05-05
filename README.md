# GDELT Text Extraction API

Welcome to the GDELT Text Extraction API project! This API is designed to facilitate the extraction of formatted JSON text from GDELT, providing a streamlined interface for data collection and analysis of news articles.

## Features

- **Streamlined Interface:** Adjust your search by tone, language, keywords, repetitions, and more.
- **Search Saving:** Save your searches and found links for easy future access.
- **JSON Extraction:** Extract text related to GDELT links in JSON format for advanced analysis.
- **Human JSON Annotation:** Streamlined Infterface allow manual annotation for misinformation/disinformation signals.
- **Simple Automation:** Easily run automated scripts to extract information on specific domains.
- **Auto-annotation:** Easily run automated annotations on Extracted Data with local LLM support.

## Installation

Go to the project folder \GDELT_scraping and create the following folders:
```bash
mkdir search_log
mkdir search_results
mkdir raw_text_data
mkdir annotated_data
```


Clone repostory, then run:
```bash
pip install -r requirements.txt
```
## Usage

You can use the dashboard by running the following command:

```bash
streamlit run DataGatheringDashboard.py
```

If you are  interested in automatic data scraping, modify AutoScraper.py with your customized filters and run:

```bash
python AutoScraper.py
```

## Acknowledgments

*This project includes code from the following repository: [GDELT Doc API](https://github.com/alex9smith/gdelt-doc-api)*.

