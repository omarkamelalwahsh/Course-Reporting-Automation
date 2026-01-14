# 🎓 Zedny Smart Course Recommender & Intelligence System

## 📝 Overview

An AI-powered system designed to provide semantic course recommendations and generate weekly intelligence reports. Built for **Zedny**, this project leverages state-of-the-art NLP models to understand user intent and deliver high-quality educational insights.

## 🚀 Key Features

- **AI-Powered Recommendation Engine**: Uses Sentence Transformers for semantic similarity search.
- **2-Stage Filtering**: Combines hard pre-filters (level, category) with soft post-filters for precision.
- **Automated Intelligence Reports**: Generates weekly reports in JSON, Markdown, HTML, and professional PDF formats.
- **Role-Based Search**: Tailored recommendations for specific job roles.
- **Interactive UI**: Built with Streamlit for a premium user experience.
- **Production-Ready API**: FastAPI backend with automated health checks and structured logging.

## 🏗️ Project Structure

```text
course-recommender/
├── app.py                  # Streamlit UI Entrypoint
├── main.py                 # Unified CLI Entrypoint (Scrape, Report, Search)
├── requirements.txt        # Unified Dependencies
├── .env.example            # Environment Template (Safe for GitHub)
├── src/                    # Core Source Code
│   ├── ai/                 # AI Engine & Recommender Pipeline
│   │   ├── engine.py       # Recommendation Engine (Semantic Search)
│   │   └── pipeline.py     # End-to-end processing logic
│   ├── scraper/            # Web Scraping & API Clients
│   │   └── client.py       # Zedny API Client
│   ├── report/             # Report Generation Logic (PDF/Excel)
│   ├── mailer/             # Email Dispatching
│   ├── api/                # FastAPI Backend
│   ├── config.py           # Settings & Env Validation (Pydantic)
│   ├── logger.py           # Unified Logging System
│   └── utils.py            # Shared Utilities
├── data/                   # Dataset & Sample Files
├── docs/                   # Documentation (EN/AR)
├── tests/                  # Unit & Smoke Tests
└── outputs/                # Local Generated Reports (Git Ignored)
```

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.8+
- [Optional] Virtual Environment (`python -m venv venv`)

### 2. Installation

```bash
pip install -r requirements.txt
```

### Running the UI

```bash
streamlit run app.py
```

### Running the API

```bash
uvicorn src.api.main:app --reload
```

### Building the Search Index

If you update the dataset, rebuild the FAISS index:

```bash
python scripts/build_index.py
```

## 🔒 Security First

- **Zero Secrets in Code**: All sensitive data is extracted to `.env`.
- **Validation**: The system performs a startup check on environment variables.
- **Ignored Files**: Logs, outputs, and `.env` are automatically excluded from Git.

## 🛠️ Troubleshooting

- **Missing Token**: If the app fails at startup, ensure `ZEDNY_AUTH_TOKEN` is set in `.env`.
- **Model Download**: On first run, the system will download the `sentence-transformers` model (~100MB).

---
*Developed for Zedny MVP.*
"# Course-Reporting-Automation" 
