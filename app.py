import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.pipeline import CourseRecommenderPipeline
from src.schemas import RecommendRequest
from src.config import TOP_K_DEFAULT

# Page Config
st.set_page_config(
    page_title="Zedny Smart Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Vibe Coding Approved)
st.markdown("""
<style>
    /* Card Container */
    .result-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease;
    }
    .result-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Rank Badge */
    .rank-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.9em;
        margin-right: 10px;
        display: inline-block;
    }
    
    /* Title Link */
    .course-title {
        font-size: 1.3em;
        font-weight: 700;
        color: #1f2937;
        text-decoration: none;
    }
    .course-title:hover {
        color: #ff4b4b;
        text-decoration: underline;
    }
    
    /* Metadata */
    .meta-tag {
        background-color: #f3f4f6;
        color: #4b5563;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        margin-right: 8px;
    }
    
    /* Explanation Section */
    .why-section {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #f0f0f0;
        font-size: 0.85em;
        color: #059669; /* Green for explanation checking */
    }
    
    /* Score */
    .score-text {
        float: right;
        color: #9ca3af;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# Application State
@st.cache_resource
def get_pipeline():
    return CourseRecommenderPipeline()

def main():
    st.title("🎓 Zedny Smart Course Recommender")
    st.caption("AI-Powered Semantic Search | Production V2")

    # 1. Initialize Pipeline (Always run)
    with st.spinner("Initializing AI Engine..."):
        try:
            pipeline = get_pipeline()
        except Exception as e:
            st.error(f"Failed to initialize system: {e}")
            st.stop()

    # 2. Sidebar Filters (Always Visible)
    st.sidebar.header("🔍 Search Filters")
    
    # Dynamic Options
    categories = ["Any"]
    levels = ["Any"]
    if pipeline.courses_df is not None:
        if 'category' in pipeline.courses_df.columns:
            categories += sorted(pipeline.courses_df['category'].dropna().unique().tolist())
        if 'level' in pipeline.courses_df.columns:
            levels += sorted(pipeline.courses_df['level'].dropna().unique().tolist())

    sel_category = st.sidebar.selectbox("Category", categories)
    sel_level = st.sidebar.selectbox("Level", levels)
    top_k = st.sidebar.slider("Number of Results", 3, 30, TOP_K_DEFAULT)
    enable_rerank = st.sidebar.checkbox("Deep Re-ranking (Slow)", value=False)
    show_debug = st.sidebar.checkbox("Show Explanation & Debug", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.info("Tip: Try searching for 'Python', 'Leadership', or 'تسويق الكتروني'")

    # 3. Main Search
    query = st.text_input("What do you want to learn today?", placeholder="e.g. Machine Learning, Project Management...")

    if query:
        # Validate input
        if len(query.strip()) < 2:
            st.warning("Please enter a longer query to get good results.")
            return

        # Construct Request
        filters = {}
        if sel_category != "Any": filters['category'] = sel_category
        if sel_level != "Any": filters['level'] = sel_level

        try:
            req = RecommendRequest(
                query=query,
                top_k=top_k,
                filters=filters,
                enable_reranking=enable_rerank
            )
            
            with st.spinner("Searching & Ranking..."):
                response = pipeline.recommend(req)

            # 4. Results Display
            st.markdown(f"### Results for `{query}`")
            
            if not response.results:
                st.warning("😕 No courses matched your query explicitly.")
                st.info("Try relaxing your filters or using broader keywords.")
                
                if show_debug:
                    with st.expander("Debug Info"):
                        st.json(response.debug_info)
            else:
                st.success(f"Found {response.total_found} relevant courses.")
                
                for res in response.results:
                    # Construct Meta Tags
                    cat_tag = f'<span class="meta-tag">📂 {res.debug_info.get("category", "General")}</span>'
                    lvl_tag = f'<span class="meta-tag">📊 {res.debug_info.get("level", "All")}</span>'
                    
                    # Construct Why Section
                    why_html = ""
                    if show_debug and res.why:
                        why_bullets = "".join([f"<li>{reason}</li>" for reason in res.why])
                        why_html = f"""
                        <div class="why-section">
                            <b>💡 Why this course?</b>
                            <ul>{why_bullets}</ul>
                        </div>
                        """
                    
                    # Card HTML
                    st.markdown(f"""
                    <div class="result-card">
                        <div>
                            <span class="rank-badge">#{res.rank}</span>
                            <a href="{res.url}" target="_blank" class="course-title">{res.title}</a>
                            <span class="score-text">Score: {res.score:.2f}</span>
                        </div>
                        <div style="margin-top: 8px; margin-bottom: 8px;">
                            {cat_tag} {lvl_tag}
                        </div>
                        <p style="color: #4b5563; line-height: 1.5;">{res.debug_info.get('desc_snippet')}...</p>
                        {why_html}
                    </div>
                    """, unsafe_allow_html=True)
                
                if show_debug:
                    st.divider()
                    st.json(response.debug_info)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            if show_debug:
                st.exception(e)

if __name__ == "__main__":
    main()
