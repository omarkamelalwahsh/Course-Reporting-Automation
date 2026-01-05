import streamlit as st
import pandas as pd
import hashlib
import os
from src.recommender import CourseRecommender

from src.recommender import CourseRecommender
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Page Configuration
st.set_page_config(
    page_title="Zedny Smart Course Recommender",
    page_icon="🎓",
    layout="wide"
)

# --- 0. Optimized Model Loading (Cached Global Resource) ---
@st.cache_resource(show_spinner="Loading AI Model (Run Once)...")
def load_all_minilm_model():
    """
    Load the SentenceTransformer model once and cache it in memory.
    This prevents re-loading/downloading on every session start.
    """
    if SentenceTransformer is None:
        return None
    return SentenceTransformer('all-MiniLM-L6-v2')

# --- 1. Session State Initialization ---
if "recommender" not in st.session_state:
    # Load model from cache
    cached_model = load_all_minilm_model()
    # Initialize recommender with cached model
    st.session_state["recommender"] = CourseRecommender(model=cached_model)
if "raw_results" not in st.session_state:
    st.session_state["raw_results"] = None
if "last_debug_info" not in st.session_state:
    st.session_state["last_debug_info"] = None
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""
if "loaded_source_hash" not in st.session_state:
    st.session_state["loaded_source_hash"] = None

# --- 2. Sidebar: Dataset & Configuration ---
with st.sidebar:
    st.header("📂 Dataset")
    uploaded_file = st.file_uploader("Upload Courses CSV", type=["csv"], help="Upload your own course dataset.")
    
    st.divider()
    
    st.header("Search Configuration")
    # Pre-Run Filters
    # We need to access the DataFrame to populate these, but it might not be loaded yet.
    # We will populate them dynamically below or use defaults.
    
    # Logic to load data if needed
    source_to_load = None
    source_hash = None
    
    if uploaded_file:
        # Compute hash of file content to detect changes
        file_bytes = uploaded_file.getvalue()
        source_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Read the file to DF
        try:
            uploaded_file.seek(0)
            df_temp = pd.read_csv(uploaded_file)
            source_to_load = df_temp
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            source_to_load = None
    else:
        # Default file
        default_path = "data/courses.csv"
        if os.path.exists(default_path):
            with open(default_path, "rb") as f:
                source_hash = hashlib.md5(f.read()).hexdigest()
            source_to_load = default_path
        else:
            source_hash = "fallback_sample"
            source_to_load = "fallback" # Special flag or just let recommender handle it? 
            # Recommender load_courses handles paths or DFs.
            # If we pass a bad path, it uses internal fallback.

    # Check if we need to (re)load
    if st.session_state["loaded_source_hash"] != source_hash:
        with st.spinner("Processing dataset (validating, embedding, caching)..."):
            try:
                # If source_to_load is "fallback", we pass a non-existent path to trigger recommender fallback?
                # Or better, pass an empty DF or let recommender handle it.
                if source_to_load == "fallback":
                    st.session_state["recommender"].load_courses("non_existent_file.csv")
                else:
                    st.session_state["recommender"].load_courses(source_to_load)
                    
                st.session_state["loaded_source_hash"] = source_hash
                st.success("Dataset loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load dataset: {e}")

    # Now we have a loaded recommender (hopefully)
    rec = st.session_state["recommender"]
    df_ref = rec.courses_df
    
    # Pre-Fill Filter Options
    if df_ref is not None and not df_ref.empty:
        pre_levels = ["Any"] + sorted(list(df_ref['level'].unique())) if 'level' in df_ref.columns else ["Any"]
        pre_categories = ["Any"] + sorted(list(df_ref['category'].unique())) if 'category' in df_ref.columns else ["Any"]
        max_dur_ref = int(df_ref['duration_hours'].max()) + 1 if 'duration_hours' in df_ref.columns else 100
    else:
        pre_levels = ["Any"]
        pre_categories = ["Any"]
        max_dur_ref = 100

    pre_level = st.selectbox("Pre-Level", pre_levels, index=0)
    pre_category = st.selectbox("Pre-Category", pre_categories, index=0)
    
    valid_max_dur = max(1, max_dur_ref)
    pre_max_duration = st.slider("Pre-Max Duration", 0, valid_max_dur, valid_max_dur)
    
    top_k_raw = st.number_input("Top K Candidates", min_value=5, max_value=100, value=30, step=5)
    
    st.divider()
    show_debug = st.checkbox("Show Debug Info", value=False)
    
    
# --- 3. Main Content: Header & Dataset Preview ---
st.title("🎓 Zedny Smart Course Recommender")

if uploaded_file and df_ref is not None:
    with st.expander("📊 Dataset Preview & Stats", expanded=True):
        st.write(f"**Total Courses:** {len(df_ref)} | **Columns:** {', '.join(df_ref.columns)}")
        st.dataframe(df_ref.head(10), use_container_width=True)
        if len(df_ref) > 5000:
            st.warning("⚠️ Large dataset (>5000 rows). Performance depends on Streamlit Cloud resources.")

# --- 4. Search UI ---
st.markdown("### 🔍 Find a Course")

# Example Queries
cols = st.columns([1, 1, 1, 1, 1, 4])
def set_q(txt): st.session_state["query_input"] = txt

if cols[0].button("ML"): set_q("ML")
if cols[1].button("NLP"): set_q("NLP")
if cols[2].button("AWS"): set_q("AWS")
if cols[3].button("Flutter"): set_q("Flutter")
if cols[4].button("BI"): set_q("BI")

query = st.text_input("What do you want to learn?", value=st.session_state["query_input"], placeholder="e.g. Python for Data Science")
search_clicked = st.button("Get Recommendations", type="primary")

# --- 5. Search Logic ---
if search_clicked:
    if not query.strip():
        st.warning("Please enter a search query.")
    elif "recommender" not in st.session_state:
        st.error("Recommender system is not initialized.")
    else:
        with st.spinner("Running AI Search..."):
            try:
                # Auto-detect advanced
                final_pre_level = pre_level
                if pre_level == "Any":
                    strong_keywords = ["advanced", "expert", "senior", "deep", "master"]
                    if any(kw in query.lower() for kw in strong_keywords):
                        final_pre_level = "Advanced"
                        st.toast(f"Detected advanced topic '{query}'. Auto-setting Level to Advanced.", icon="🧠")
                
                pre_filters = {
                    "level": final_pre_level,
                    "category": pre_category,
                    "max_duration": pre_max_duration
                }
                
                response = rec.recommend(
                    query, 
                    top_k=top_k_raw,
                    pre_filters=pre_filters,
                    similarity_threshold=0.25
                )
                
                results = response.get("results", [])
                debug_info = response.get("debug_info", {})
                
                st.session_state["last_debug_info"] = debug_info
                
                if debug_info.get("keyword_warning"):
                     st.warning(debug_info["keyword_warning"])
                     st.session_state["raw_results"] = pd.DataFrame()
                elif results:
                    st.session_state["raw_results"] = pd.DataFrame(results)
                    # Force session state update? Not strictly needed for DF but good practice
                else:
                    st.session_state["raw_results"] = pd.DataFrame() 
                    st.warning("No strong matches found. Try changing your query or relax filters.")
                    
            except Exception as e:
                st.error(f"An error occurred during search: {e}")

# --- 6. Debug Panel ---
if show_debug and st.session_state.get("last_debug_info"):
    with st.expander("🛠️ Debug Information", expanded=True):
        d_info = st.session_state["last_debug_info"]
        st.write(f"**Original Query:** `{d_info.get('query')}`")
        st.write(f"**Expanded Query:** `{d_info.get('expanded_query')}`")
        st.write(f"**Courses after pre-filter:** `{d_info.get('pre_filter_count')}` / `{d_info.get('total_courses')}`")
        
        scores = d_info.get('top_raw_scores', [])
        if scores:
            st.write(f"**Top 5 Raw Similarity Scores:** `{[round(s, 4) for s in scores]}`")
        else:
            st.write("**Top 5 Raw Similarity Scores:** None")
            
        if d_info.get("keyword_warning"):
            st.error(f"**Guardrail Warning:** {d_info.get('keyword_warning')}")


# --- 7. Results & Post-Filters ---
if st.session_state["raw_results"] is not None and not st.session_state["raw_results"].empty:
    st.divider()
    st.header("Refine Results")
    
    df = st.session_state["raw_results"].copy()
    
    # Post-Filters
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        post_levels = ["Any"] + sorted(list(df['level'].unique())) if 'level' in df.columns else ["Any"]
        post_level = st.selectbox("Post-Level", post_levels, key="post_lvl")
        
    with c2:
        post_categories = ["Any"] + sorted(list(df['category'].unique())) if 'category' in df.columns else ["Any"]
        post_category = st.selectbox("Post-Category", post_categories, key="post_cat")
        
    with c3:
        max_post_dur_val = int(df['duration_hours'].max()) + 1 if 'duration_hours' in df.columns else 100
        post_duration_cap = st.slider("Max Duration", 0, max_post_dur_val, max_post_dur_val, key="post_dur")
        
    with c4:
        res_count = len(df)
        post_top_n = st.slider("Show Results", 1, res_count, min(5, res_count), key="post_topn")
    
    # Apply Post Filters
    filtered_df = df.copy()
    if post_level != "Any":
        filtered_df = filtered_df[filtered_df['level'] == post_level]
    if post_category != "Any":
        filtered_df = filtered_df[filtered_df['category'] == post_category]
    if 'duration_hours' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['duration_hours'] <= post_duration_cap]
        
    display_df = filtered_df.head(post_top_n)
    
    st.subheader(f"Showing {len(display_df)} results")
    
    if display_df.empty:
        st.warning("No courses match your POST-filters.")
    else:
        for idx, row in display_df.iterrows():
            with st.container():
                rank_display = f"{row.get('rank', 0)}/10"
                
                col_main, col_meta = st.columns([3, 1])
                with col_main:
                    st.markdown(f"### {row['title']}")
                    st.markdown(f"**Description:** {row['description']}")
                    st.markdown(f"**Skills:** `{row['skills']}`")
                with col_meta:
                    st.metric(label="Relevance Fit", value=rank_display)
                    st.caption(f"**Category:** {row['category']}")
                    st.caption(f"**Level:** {row['level']}")
                    st.caption(f"**Duration:** {row['duration_hours']}h")
                
                st.divider()
elif st.session_state["raw_results"] is None:
    st.info("👈 Upload a dataset or use the default one, then search to start.")
