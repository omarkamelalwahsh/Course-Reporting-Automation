# 📘 Zedny Smart Course Recommender - Technical Documentation

## 1. Project Overview

The Zedny Smart Course Recommender is an AI-powered search engine designed to solve the "discovery problem" in e-learning. Unlike traditional keyword search, it understands **semantic intent** (e.g., matching "ML" to "Machine Learning" or "coding" to "Python").

It is designed as a **Zero-Config, Plug-and-Play** solution. The system automatically adapts to any course dataset provided in CSV format, validates the schema, and builds a custom search index on the fly.

---

## 2. System Architecture

The application follows a modular architecture:

```mermaid
graph TD
    User[User Interface (Streamlit)] <--> |Query & Filters| Controller[App Logic (app.py)]
    Controller <--> |Get Recommendations| Engine[Recommender Engine (src/recommender.py)]
    Engine <--> |Load/Cache| DataMgr[Data Manager (src/utils.py)]
    Engine <--> |Encode Text| AI[AI Model (SentenceTransformer)]
    DataMgr <--> |Read/Write| Storage[File System (data/ & outputs/)]
```

### Components

1. **Streamlit App (`app.py`)**: Handles user interaction, state management, and optimized resource loading.
2. **Recommender Engine (`src/recommender.py`)**: The core class responsible for vector search, similarity ranking, and business logic guardrails.
3. **Data Manager (`src/utils.py`)**: Handles data ingestion, schema normalization, auto-cleaning, and abbreviation mining.

---

## 3. The AI Model

### Model Selection

We reuse the **`all-MiniLM-L6-v2`** model from the `sentence-transformers` library.

- **Type**: BERT-based Sentence Transformer.
- **Dimensions**: 384-dimensional dense vector space.
- **Why this model?**: It provides the best trade-off between **speed** and **accuracy**. It is lightweight (~90MB), making it ideal for CPU-based deployment (like Streamlit Cloud) while maintaining state-of-the-art semantic understanding.

### How it Works

1. **Encoding**: The system converts every course's "Combined Text" (Title + Skills + Description) into a 384-d vector.
2. **Indexing**: These vectors are stored in memory (and cached to disk).
3. **Search**: When a user queries, the query is converted to a vector. We calculate the **Cosine Similarity** between the query vector and all course vectors.
4. **Ranking**: Courses are ranked by their similarity score (0.0 to 1.0).

---

## 4. Key Features & "Fine-Tuning" Logic

### A. Zero-Shot Domain Adaptation (Auto-Abbreviation)

We generally do not "fine-tune" the model weights (which requires GPU training). Instead, we use **In-Context Adaptation**:

- **Problem**: Generic models don't know that "NLP" matches "Natural Language Processing" strongly enough.
- **Solution**: The system scans the dataset for patterns like `Title (ABBR)` or acronyms in the `Skills` column.
- **Mechanism**: It builds a dynamic dictionary (e.g., `{'nlp': 'natural language processing nlp'}`).
- **Query Expansion**: When a user searches for "NLP", the system transparently expands it to "natural language processing nlp" before sending it to the AI. This effectively "teaches" the model the jargon without retraining.

### B. Performance Caching strategy

To ensure instant load times:

1. **Hash-Based Caching**: We calculate an MD5 hash of the dataset content.
2. **Artifact Storage**: Embeddings and metadata are saved to `outputs/embeddings_<hash>.npy`.
3. **Lazy Loading**: On startup, if the hash matches, we load from disk (milliseconds) instead of re-computing (seconds/minutes).
4. **Memory Persistence**: `@st.cache_resource` keeps the heavy AI model in RAM across user sessions.

### C. Keyword Guardrails 2.0

To prevent AI hallucinations (providing irrelevant results with low confidence):

1. **Regex Tokenization**: We clean the query (handling punctuation like "won't" -> "wont").
2. **Smart Stopwords**: We ignore common conversational words ("I want to learn", "please", "advanced").
3. **Validation**: If the remaining specific keywords (e.g., "Flutter") do not exist *anywhere* in the filtered dataset, the system halts semantic search and shows a specific error.

---

## 5. Filtering Logic

The system uses a **Funnel Approach** for maximum precision:

1. **Pre-Filtering (Hard)**:
    - SQL-like filtering on `Level`, `Category`, and `Duration`.
    - Applied *before* the AI search to reduce the search space and ensure strict adherence to constraints.
2. **Semantic Search (Soft)**:
    - Finds the best matches within the allowed subset.
3. **Post-Filtering (Refinement)**:
    - UI sliders allow the user to narrow down the results *after* seeing them (e.g., "Show only the shortest 3 courses from these results").

---

## 6. Future "Fine-Tuning" Capabilities

If the current Zero-Shot performance is insufficient, true Fine-Tuning can be implemented:

1. **Contrastive Learning**: Create pairs of `(Query, Relevant_Course)` and `(Query, Irrelevant_Course)`.
2. **Training**: Use `SentenceTransformer.fit()` with a `ContrastiveLoss` function.
3. **Deployment**: Save the new weights to a folder and load `CourseRecommender(model_name='path/to/custom/model')`.

*Note: For this MVP, the Auto-Abbreviation logic usually solves 90% of domain-specific issues without the complexity of training.*
