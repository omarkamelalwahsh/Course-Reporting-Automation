# 🎓 Zedny Smart Course Recommender

## Executive Summary

### Business Context

In the rapidly growing E-Learning market, learners face **information overload**. Traditional keyword search often fails to understand **semantic intent**. This AI-powered system solves this by:

1. **Understanding Intent**: Using Sentence Transformers for semantic search.
2. **Ensuring Relevance**: Using hard pre-filters and keyword guardrails to prevent hallucinations.
3. **Interactive Exploration**: Allowing 2-stage filtering (Pre-search & Post-search) for maximum control.

### AI Solution

This MVP leverages **Sentence Transformers (`all-MiniLM-L6-v2`)** to create semantic embeddings.

- **Pre-Filtering**: Hard filters (SQL-like) reduce the search space logic first.
- **Semantic Search**: Computes Cosine Similarity on the filtered subset.
- **Post-Filtering**: Instant UI filters refine the top results without re-running the AI.
- **Relevance Scoring**: Normalizes scores to a user-friendly **0-10 Integer Rank**.

## Key Features

- **2-Stage Filtering**:
  - **Pre-Run (Hard)**: Filter by Level, Category, Duration *before* search (Critical for performance & accuracy).
  - **Post-Run (Soft)**: Instantly slice & dice the matching results.
- **Smart Ranking**:
  - **Integer Rank (0/10)**: Easy to understand score.
  - **Similarity Thresholds**: Automatically hides weak matches (<25%).
- **Keyword Guardrails**: Warns if specific queries (e.g. "Flutter") exist in the query but not in the datset.
- **Auto-Level Detection**: Automatically detects "Advanced" intent (e.g., "Deep Learning", "Expert") and sets the filter accordingly.
- **Debug Mode**: Toggle visibility of raw similarity scores and engine logic.

## How to Run

### Prerequisites

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

The app will open at `http://localhost:8501`.

### Usage Guide

1. **Sidebar Configuration (Pre-Run)**:
    - **Query**: Enter what you want to learn (e.g., "Python for Data Science").
    - **Pre-Level**: "Any" (Auto-detects) or specific (Beginner/Intermediate/Advanced).
    - **Pre-Category**: Filter by domain.
    - **Top K**: How many AI candidates to fetch.
    - **Show Debug Info**: Check this to see raw scores.

2. **Get Recommendations**: Click the button. The AI searches *only* the filtered subset.

3. **Review & Refine (Post-Run)**:
    - The main view shows the **Filter Results** section.
    - Use slides and dropdowns to narrow down the recommended list instantly.
    - See the **Relevance Rank (X/10)** for each card.

## Project Structure

```
zedny-course-recommender/
├── app.py                      # Main Streamlit Application (UI + Logic)
├── src/
│   ├── recommender.py          # AI Engine (Embeddings, Ranking, Guardrails)
│   ├── utils.py                # Data loading & formatting
├── data/
│   └── courses.csv             # Dataset
├── outputs/                    # Logs (optional)
├── requirements.txt            # Dependencies
└── README.md                   # Documentation
```

## Technical Details

### Architecture

1. **Hard Filters**: Pandas masking on `level`, `category`, `duration`.
2. **Embedding Slice**: The system creates/accesses embeddings *only* for the filtered indices.
3. **Semantic Similarity**: `Cosine(Query_Vector, Subset_Vectors)`.
4. **Thresholding**: Drops results with `score < 0.25`.
5. **Ranking**: `MinMaxScale(Scores) * 10` -> Rounded to Integer.

### Dependencies

- `streamlit`: UI
- `sentence-transformers`: AI Model
- `pandas` & `numpy`: Data Processing
- `scikit-learn`: Cosine Similarity

## License

Educational MVP for Zedny.
