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
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .result-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 5px solid #ff4b4b;
    }
    .rank-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
    }
    .score {
        color: #666;
        font-size: 0.8em;
    }
    a {
        text-decoration: none;
        color: #000;
        font-weight: bold;
        font-size: 1.1em;
    }
    a:hover {
        color: #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# Application State
@st.cache_resource
def get_pipeline():
    return CourseRecommenderPipeline()

def main():
    st.title("🎓 Zedny Smart Course Recommender")
    st.caption("AI-Powered Semantic Search | production-v2")

    with st.spinner("Initializing AI Engine..."):
        try:
            pipeline = get_pipeline()
        except Exception as e:
            st.error(f"Failed to initialize system: {e}")
            st.stop()

    # Sidebar Filters
    st.sidebar.header("🔍 Search Filters")
    top_k = st.sidebar.slider("Number of Results", 5, 50, TOP_K_DEFAULT)
    
    # Extract unique values for filters (if df is loaded)
    categories = ["Any"]
    levels = ["Any"]
    if pipeline.courses_df is not None:
        categories += sorted(pipeline.courses_df['category'].dropna().unique().tolist())
        levels += sorted(pipeline.courses_df['level'].dropna().unique().tolist())

    sel_category = st.sidebar.selectbox("Category", categories)
    sel_level = st.sidebar.selectbox("Level", levels)
    enable_rerank = st.sidebar.checkbox("Enable Deep Re-ranking (Slow)", value=False)
    show_debug = st.sidebar.checkbox("Show Debug Info", value=False)

    # Main Search
    query = st.text_input("What do you want to learn today?", placeholder="e.g. Python, Machine Learning, Leadership...")

    if query:
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
            
            with st.spinner("Thinking..."):
                response = pipeline.recommend(req)

            if not response.results:
                st.warning(f"No relevant courses found for '{query}'. Try a different keyword.")
                if show_debug:
                    st.json(response.debug_info)
            else:
                st.write(f"Found **{response.total_found}** relevant courses.")
                
                for res in response.results:
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="rank-badge">#{res.rank}</span>
                            <a href="{res.url}" target="_blank">{res.title}</a>
                            <p>{res.debug_info.get('desc_snippet')}...</p>
                            <span class="score">Relevance Score: {res.score:.4f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                if show_debug:
                    st.divider()
                    st.subheader("Debug Information")
                    st.json(response.debug_info)

        except Exception as e:
            st.error(f"Error processing request: {e}")
            if show_debug:
                st.exception(e)

if __name__ == "__main__":
    main()
