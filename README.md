# Zedny Smart Course Recommender (MVP)

> **Principal AI Engineer Implementation**
>
> A robust, production-ready Semantic Search & Recommendation engine built with strict relevance gating, multilingual support, and structured pipeline architecture.

## 🚀 Key Features

* **Multilingual Semantic Search:** Supports Arabic & English queries with automatic translation (`"كورس بايثون"` -> `"python"`).
* **Strict Relevance Gating:** Zero hallucinations. Returns "No results" rather than invalid guesses.
* **Offline-First:** Uses local FAISS index and pre-computed embeddings. No API keys required.
* **1-10 Smart Ranking:** Normalized integer scoring for easy UI display.
* **Deep Re-ranking (Optional):** Uses Cross-Encoder for high-precision validation.

## 📂 Project Structure

```
c:\course-recommender\
├── app.py                  # Streamlit UI Entry Point
├── main.py                 # CLI Entry Point
├── src/
│   ├── ai/                 # Core AI Logic
│   │   ├── embeddings.py   # SentenceTransformer Wrapper
│   │   ├── gating.py       # Strict/Semantic Gating Logic
│   │   └── ranker.py       # Score Normalization
│   ├── pipeline.py         # Main Orchestrator
│   ├── config.py           # Constants & Config
│   ├── logger.py           # Structured JSON Logger
│   ├── schemas.py          # Pydantic Input/Output Models
│   └── utils.py            # Text Normalization & Tools
├── data/                   # Dataset & Indices
│   ├── courses.csv         # Raw Data
│   └── faiss.index         # Vector Index
├── scripts/
│   └── build_index.py      # Offline Index Builder
└── tests/                  # Unit Tests
```

## 🛠️ Installation

**Prerequisites:** Python 3.10+ (Windows/Linux/Mac)

1. **Clone & Install Dependencies**

    ```powershell
    pip install -r requirements.txt
    ```

2. **Build Offline Index** (Must run once)

    ```powershell
    python scripts/build_index.py
    ```

    *Expect "Saving embeddings to data/course_embeddings.npy..."*

## 🏃‍♂️ Usage

### 1. Web UI (Streamlit)

The primary interface for users.

```powershell
python -m streamlit run app.py
```

* Opens in your browser at `http://localhost:8502`.
* Try queries: `Python`, `Machine Learning`, `كورس بايثون`.

### 2. CLI (Command Line)

For quick testing and automation.

```powershell
python main.py "machine learning" --top_k 5
```

## 🧪 Testing

Run the rigorous test suite to verify relevance and strict gating.

```powershell
python -m pytest tests/test_recommender.py
```

## ⚠️ Troubleshooting

| Error | Fix |
| :--- | :--- |
| `Index missing` | Run `python scripts/build_index.py` |
| `ModuleNotFoundError` | Ensure you run from root `c:\course-recommender` |
| `OpenAI API Key missing` | Not needed! This project is 100% offline. |

---
**Version:** 2.0.0 (Principal MVP Refactor)
**Author:** Antigravity (Google DeepMind)
