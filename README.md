# 🎓 Zedny Smart Course Recommender

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://course-recommender-nguwc5gsetcqywddjhrwxm.streamlit.app)

## Executive Summary

**Zedny Smart Course Recommender** is an Intelligent, Zero-Config Search Engine designed to help students find the right courses instantly. It goes beyond simple keywords by understanding the *meaning* of what you want to learn.

**Current Status**: `v2.1 (Fully Automatic)`

- **Live Deployment Ready**
- **Zero-Touch Startup**: No manual upload needed; just run and search.
- **Self-Healing**: Automatically fixes data schema issues.
- **Smart & Fast**: Caches AI models for instant performance.

---

## 📖 Full Documentation

For a deep dive into the Architecture, AI Model, and Customization, please read the **[Technical Documentation](DOCUMENTATION.md)**.

---

## Key Features

### 🚀 Smart AI Engine

- **Semantic Search**: Understands that "ML" = "Machine Learning" and "coding" = "Programming".
- **Auto-Learning**: Automatically detects acronyms in your dataset (e.g., `NLP`, `AWS`) and learns their full forms without you doing anything.
- **Accuracy Guardrails**: Smartly filters out irrelevant results and warns you if your query has no match in the database.

### ⚡ Automatic & Fast

- **Pre-Cached Models**: The heavy AI brain is loaded once; subsequent searches are milliseconds fast.
- **Data Caching**: Dataset embeddings are saved to disk (`outputs/`) so the app starts up instantly after the first run.
- **Error Handling**: Gracefully handles single results or empty searches with clear, helpful messages.

### 🎛️ Precision Filtering

1. **Level & Category Filters**: Narrow down by difficulty or topic *before* searching.
2. **Duration Control**: Filter out courses that are too long or too short.
3. **Post-Refinement**: Tweak the results list instantly with UI sliders.

---

## How to Run

### 1. Installation

Ensure you have Python 3.8+ installed.

```bash
git clone https://github.com/omarkamelalwahsh/course-recommender.git
cd course-recommender
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## Usage Guide

1. **Search**: Just type what you want (e.g., "Python for data science" or "web dev").
2. **Filter**: Use the sidebar to set your level (Beginner/Advanced) or Category.
3. **Refine**: If you get too many results, use the sliders below the search bar to narrow them down.

*Note: If you search for something completely unrelated (e.g., "Cooking"), the system will show an error indicating that no matching content exists.*

---

## Project Structure

```
zedny-course-recommender/
├── app.py                      # Main Application Entry Point
├── DOCUMENTATION.md            # Detailed Technical Docs
├── requirements.txt            # Python Dependencies
├── data/
│   └── courses.csv             # The Course Dataset
├── src/
│   ├── recommender.py          # AI Engine & Logic
│   └── utils.py                # Data Processing & Caching
└── outputs/                    # Auto-generated cache files
```

## License

Educational MVP for Zedny.
