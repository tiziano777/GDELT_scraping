# GDELT Text Extraction API

Welcome to the **GDELT Text Extraction API** project — a toolkit designed to streamline the extraction, processing, and annotation of structured JSON data from GDELT (Global Database of Events, Language, and Tone). This interface supports efficient collection and analysis of news content, with both manual and automated workflows.

---

## 🔍 Core Features

* **Flexible Search Interface**: Customize queries by tone, language, keywords, repetition thresholds, and more.
* **Search Persistence**: Save search configurations and retrieved URLs for future reuse.
* **Structured Output**: Extract article content as well-formatted JSON, ready for downstream NLP tasks.
* **Manual Annotation Tool**: Web-based interface to annotate disinformation/misinformation signals in JSON format.
* **Automated Processing**: Easily execute scripted routines for targeted domain-level data collection.
* **Auto-Annotation Support**: Annotate extracted content using local LLMs in batch mode.

---

## ⚙️ Installation

Clone the repository, create venv and install dependencies:

```bash
git clone https://github.com/tiziano777/GDELT_scraping
cd GDELT_scraping
python -m venv gdelt_env
pip install -r requirements.txt
```

Navigate to the `GDELT_scraping` root directory and create the following subfolders:

```bash
mkdir src/search_log
mkdir src/search_results
mkdir src/raw_text_data
mkdir src/annotated_data
mkdir src/EDA/topic
```

---

## 🚀 Usage

To launch the interactive dashboard, run:

```bash
streamlit run DataGatheringDashboard.py
```

For automatic data scraping, customize the filters in `AutoScraper.py` and execute:

```bash
python AutoScraper.py
```

---

## 📊 EDA Module

The EDA component supports:

* Aggregation of collected article metadata
* Clustering by user-defined topical categories
* Exploratory analyses via word frequency statistics (wordFrequence Folder)

To aggregate data from the `raw_text_data` directory:

```bash
cd src/EDA
python aggregate_results.py
```

To assign articles to topics:

1. Edit the `create_keyword_sets()` function in `similarity_layer.py`, using the provided JSON schema.
2. Then run:

```bash
python similarity_layer.py
```

---

## 📄 Acknowledgments

This project incorporates and builds upon components from the following open-source repository: [GDELT Doc API](https://github.com/alex9smith/gdelt-doc-api).
