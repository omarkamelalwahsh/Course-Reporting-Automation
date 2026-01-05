import streamlit as st
import pandas as pd
from src.recommender import CourseRecommender
import time

# Page Configuration
st.set_page_config(
    page_title="Zedny Smart Course Recommender",
    page_icon="🎓",
    layout="wide"
)

# Initialize Recommender in Session State (Singleton pattern)
if "recommender" not in st.session_state:
    with st.spinner("Initializing AI Recommender System..."):
        try:
            rec = CourseRecommender()
            rec.load_courses("data/courses.csv")
            st.session_state["recommender"] = rec
        except Exception as e:
            st.error(f"Failed to initialize recommender: {e}")

# Initialize raw results storage
if "raw_results" not in st.session_state:
    st.session_state["raw_results"] = None
if "last_debug_info" not in st.session_state:
    st.session_state["last_debug_info"] = None

# Sidebar - PRE-RUN Configuration
with st.sidebar:
    st.header("Search Configuration")
    query = st.text_input("What do you want to learn?", placeholder="e.g. Python for Data Science")
    
    st.divider()
    st.markdown("### Pre-Run Filters Hard")
    st.caption("Filters applied BEFORE Artificial Intelligence search.")
    
    # Pre-Run Level Filter
    if "recommender" in st.session_state and st.session_state["recommender"].courses_df is not None:
        df_ref = st.session_state["recommender"].courses_df
        pre_levels = ["Any"] + sorted(list(df_ref['level'].unique())) if 'level' in df_ref.columns else ["Any"]
        pre_categories = ["Any"] + sorted(list(df_ref['category'].unique())) if 'category' in df_ref.columns else ["Any"]
        max_dur_ref = int(df_ref['duration_hours'].max()) + 1 if 'duration_hours' in df_ref.columns else 100
    else:
        pre_levels = ["Any", "Beginner", "Intermediate", "Advanced"]
        pre_categories = ["Any"]
        max_dur_ref = 100

    pre_level = st.selectbox("Pre-Level", pre_levels, index=0, key="pre_level_box")
    pre_category = st.selectbox("Pre-Category", pre_categories, index=0, key="pre_cat_box")
    
    # FIX: Slider Crash Prevention
    valid_max_dur = max(1, max_dur_ref)
    pre_max_duration = st.slider("Pre-Max Duration", 0, valid_max_dur, valid_max_dur, key="pre_dur_slide")
    
    top_k_raw = st.number_input("Top K Candidates", min_value=5, max_value=100, value=30, step=5)
    
    st.divider()
    show_debug = st.checkbox("Show Debug Info", value=False)
    
    search_clicked = st.button("Get Recommendations", type="primary")

# Search Logic
if search_clicked:
    if not query.strip():
        st.warning("Please enter a search query.")
    elif "recommender" not in st.session_state:
        st.error("Recommender system is not initialized.")
    else:
        with st.spinner("Applying filters & running semantic search..."):
            try:
                # 3. Check for automatic Advanced boost if Any is selected
                final_pre_level = pre_level
                if pre_level == "Any":
                    strong_keywords = ["advanced", "expert", "senior", "deep", "master"]
                    if any(kw in query.lower() for kw in strong_keywords):
                        final_pre_level = "Advanced"
                        st.toast(f"Detected advanced topic '{query}'. Auto-setting Level to Advanced.", icon="🧠")
                
                # Build Pre-Filters
                pre_filters = {
                    "level": final_pre_level,
                    "category": pre_category,
                    "max_duration": pre_max_duration
                }
                
                # Task 1: Generate raw results with Pre-Filters
                # Update: Recommend now returns Dict with results and debug_info
                response = st.session_state["recommender"].recommend(
                    query, 
                    top_k=top_k_raw,
                    pre_filters=pre_filters,
                    similarity_threshold=0.25 # Adjustable threshold
                )
                
                results = response.get("results", [])
                debug_info = response.get("debug_info", {})
                
                st.session_state["last_debug_info"] = debug_info
                
                if debug_info.get("keyword_warning"):
                     st.warning(debug_info["keyword_warning"])
                     st.session_state["raw_results"] = pd.DataFrame()
                elif results:
                    st.session_state["raw_results"] = pd.DataFrame(results)
                else:
                    st.session_state["raw_results"] = pd.DataFrame() 
                    st.warning("No strong matches found. Try changing your query or relax filters.")
                    
            except Exception as e:
                st.error(f"An error occurred during search: {e}")

# Main Content
st.title("🎓 Zedny Smart Course Recommender")

# Debug Panel
if show_debug and st.session_state.get("last_debug_info"):
    with st.expander("🛠️ Debug Information", expanded=True):
        d_info = st.session_state["last_debug_info"]
        st.write(f"**Query:** `{d_info.get('query')}`")
        st.write(f"**Courses after pre-filter:** `{d_info.get('pre_filter_count')}` / `{d_info.get('total_courses')}`")
        
        scores = d_info.get('top_raw_scores', [])
        if scores:
            st.write(f"**Top 5 Raw Similarity Scores:** `{[round(s, 4) for s in scores]}`")
        else:
            st.write("**Top 5 Raw Similarity Scores:** None")
            
        if d_info.get("keyword_warning"):
            st.error(f"**Guardrail Warning:** {d_info.get('keyword_warning')}")


# Display Results & POST-Run Filters
if st.session_state["raw_results"] is not None and not st.session_state["raw_results"].empty:
    st.divider()
    st.header("Filter Results (Post-Processing)")
    st.caption("Refine the search results without re-running AI.")
    
    df = st.session_state["raw_results"].copy()
    
    # Task 2: Post-Filtering Section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Pre-filter logic ensures we only have selected level if not "Any"
        post_levels = ["Any"] + sorted(list(df['level'].unique())) if 'level' in df.columns else ["Any"]
        post_level = st.selectbox("Post-Level", post_levels, key="post_lvl")
        
    with col2:
        post_categories = ["Any"] + sorted(list(df['category'].unique())) if 'category' in df.columns else ["Any"]
        post_category = st.selectbox("Post-Category", post_categories, key="post_cat")
        
    with col3:
        # FIX: Slider Crash Prevention
        max_post_dur_val = int(df['duration_hours'].max()) + 1 if 'duration_hours' in df.columns else 100
        
        if max_post_dur_val > 0:
            post_duration_cap = st.slider("Max Duration", 0, max_post_dur_val, max_post_dur_val, key="post_dur")
        else:
            post_duration_cap = 0
            st.caption("Duration fixed: 0h")
        
    with col4:
        # FIX: Slider Crash Prevention
        res_count = len(df)
        if res_count > 1:
            post_top_n = st.slider("Show Results", 1, res_count, min(5, res_count), key="post_topn")
        else:
            post_top_n = res_count
            st.caption(f"Showing {res_count} result")
    
    # Apply Post Filters (Instant)
    filtered_df = df.copy()
    
    if post_level != "Any":
        filtered_df = filtered_df[filtered_df['level'] == post_level]
        
    if post_category != "Any":
        filtered_df = filtered_df[filtered_df['category'] == post_category]
        
    if 'duration_hours' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['duration_hours'] <= post_duration_cap]
        
    # Cap results
    display_df = filtered_df.head(post_top_n)
    
    st.subheader(f"Showing {len(display_df)} results")
    
    if display_df.empty:
        st.warning("No courses match your POST-filters.")
    else:
        # Display Cards
        for idx, row in display_df.iterrows():
            with st.container():
                rank_display = f"{row.get('rank', 0)}/10"
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {row['title']}")
                    st.markdown(f"**Description:** {row['description']}")
                    st.markdown(f"**Skills:** `{row['skills']}`")
                with c2:
                    st.metric(label="Relevance Rank", value=rank_display)
                    st.caption(f"**Category:** {row['category']}")
                    st.caption(f"**Level:** {row['level']}")
                    st.caption(f"**Duration:** {row['duration_hours']}h")
                
                st.divider()

elif st.session_state["raw_results"] is not None and st.session_state["raw_results"].empty:
     # Already warned above regarding no matches or guardrail.
     pass
else:
    st.info("Enter a query and configure filters in the sidebar to get started.")
