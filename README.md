# 🎓 Zedny Smart Course Recommender (v2.0 - Sellable)

## Executive Summary

### Product Vision

Transforming from a hardcoded prototype to a **dataset-agnostic** product. Any user or organization can now upload their course catalog (CSV), and the AI automatically adapts, validates the schema, and builds a custom semantic search engine in seconds.

### Key Innovations

1. **Plug & Play Data**: Upload your own courses; the system auto-fixes missing columns and normalizes data.
2. **Zero-Config Domain Adaptation**:
    - Automatically learns abbreviations (e.g., "NLP" -> "Natural Language Processing") from the dataset.
    - No manual dictionary maintenance required.
3. **Performance Caching**: Embeddings are computed once per uniqueness hash and saved to disk. Reloads are instant.
4. **Optimized Resource Usage**: The AI model is loaded into memory only once per server instance, ensuring fast multi-user support in Streamlit.

## Features

- **📂 Bring Your Own Data**:
  - Upload CSV via sidebar.
  - **Auto-Validation**: Fixes schema issues, fills missing values, normalizes levels (Beginner/Intermediate/Advanced).
  - **Smart Fallback**: Uses a default dataset if no file is provided.
- **🚀 Advanced Search Engine**:
  - **Semantic Search**: Understands "machine learning" matches "AI" or "deep learning".
  - **Pre-Filtering**: Hard SQL-like filters for Level, Category, and Duration.
  - **Post-Filtering**: Instant UI refinement of results.
- **🧠 Auto-Intelligence**:
  - **Abbreviation Extraction**: Scans text and skills to map acronyms (e.g., `AWS` -> `aws a w s`, `BI` -> `business intelligence`).
  - **Level Detection**: Auto-detects "Advanced" queries.
- **🛡️ Guardrails**:
  - Dataset size warnings (>5000 rows).
  - keyword warnings ('Flutter' query but no 'Flutter' in filtered data).

## How to Run

### prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`. Since the model is cached via `@st.cache_resource`, the first run downloads/loads the model, and subsequent refreshes are instant.

## Usage Guide

1. **Upload Dataset (Optional)**:
    - Use the sidebar file uploader.
    - Preview the parsed data and check for validation warnings.
2. **Configure Search**:
    - Type a query or click an Example Query button (e.g., "ML", "AWS").
    - Select Pre-Filters (Level, Category).
3. **Analyze Results**:
    - View the top semantic matches.
    - See the **Relevance Fit (0-10)**.
    - Use Post-Filters to narrow down the list further.

## Project Structure

```
zedny-course-recommender/
├── app.py                      # UI, Model Caching, Search Logic
├── src/
│   ├── recommender.py          # Core Engine (Hybrid Search, Embeddings)
│   ├── utils.py                # Validation, Cleaning, Abbreviation Extraction, Hashing
├── data/
│   └── courses.csv             # Default Dataset
├── outputs/                    # Cached Embeddings, Maps, and Logs (Auto-generated)
├── requirements.txt            # Dependencies
└── README.md                   # Documentation
```

## Technical Details

### Performance Optimization

- **Model Caching**: `streamlit.cache_resource` ensures the 90MB BERT model is loaded only once across sessions.
- **Embedding Caching**: MD5 hash of the dataset content is used to key cached `.npy` files.
- **Vector Operations**: Uses `numpy` and `scikit-learn` for fast cosine similarity blocking.

### Schema auto-fix Rules

- **Missing Columns**: Created with default values (Category="General", Level="Beginner").
- **Level Normalization**: distinct values like 'jun', 'intro' -> 'Beginner'; 'expert', 'deep' -> 'Advanced'.
- **Duration**: Extracted regex `(\d+)` from strings.

## License

Educational MVP for Zedny.
