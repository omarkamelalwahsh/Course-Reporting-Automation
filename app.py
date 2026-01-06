
import streamlit as st
import pandas as pd
import time
from src.pipeline import CourseRecommenderPipeline
from src.schemas import RecommendRequest
from src.config import TOP_K_DEFAULT

# --- Page Config ---
st.set_page_config(
    page_title="المقترح الذكي للكورسات - زدني",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Validations ---
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None

@st.cache_resource
def get_pipeline():
    return CourseRecommenderPipeline()

# --- Custom CSS for Cards & RTL ---
st.markdown("""
<style>
    /* Force RTL Layout */
    .element-container, .stMarkdown, .stText, .stTextInput, .stMultiSelect, .stSlider {
        direction: rtl; 
        text-align: right;
    }
    
    .course-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.2s;
        direction: rtl;
        text-align: right;
    }
    .course-card:hover {
        transform: scale(1.02);
        border-color: #4CAF50;
    }
    .course-title {
        font-size: 20px;
        font-weight: bold;
        color: #4CAF50 !important;
        text-decoration: none;
        margin-bottom: 5px;
        display: block;
    }
    .course-meta {
        color: #888;
        font-size: 14px;
        margin-bottom: 10px;
    }
    .course-desc {
        color: #ddd;
        font-size: 15px;
        line-height: 1.5;
    }
    .score-badge {
        background-color: #2c2c2c;
        color: #4CAF50;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 12px;
        margin-left: 10px;
        font-weight: bold;
    }
    .why-section {
        margin-top: 10px;
        padding: 10px;
        background-color: #262626;
        border-radius: 5px;
        font-size: 13px;
        color: #aaa;
    }
    .stAlert { direction: rtl; }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("<h1 style='text-align: right; color: #4CAF50;'>🎓 المقترح الذكي للكورسات</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: right; color: #888;'>محرك ذكاء اصطناعي للبحث عن الكورسات بدقة عالية</h4>", unsafe_allow_html=True)

    # Init Pipeline
    if st.session_state.pipeline is None:
        with st.spinner("جاري تحميل محرك الذكاء الاصطناعي..."):
            try:
                st.session_state.pipeline = get_pipeline()
            except Exception as e:
                st.error(f"فشل التحميل: {e}")
                st.stop()

    pipeline = st.session_state.pipeline

    # --- Sidebar Filters ---
    st.sidebar.header("🔍 خيارات البحث")
    
    # Extract categories
    categories = ["الكل"]
    levels = ["الكل"]
    
    if pipeline.courses_df is not None:
        cats = sorted(pipeline.courses_df['category'].dropna().unique().tolist())
        levs = sorted(pipeline.courses_df['level'].dropna().unique().tolist())
        categories += cats
        levels += levs

    sel_category = st.sidebar.selectbox("التصنيف", categories)
    sel_level = st.sidebar.selectbox("المستوى", levels)
    top_k = st.sidebar.slider("عدد النتائج", 5, 50, TOP_K_DEFAULT)
    
    enable_rerank = st.sidebar.checkbox("تفعیل الترتيب العميق (أبطأ ولكن أدق)", value=False)
    show_debug = st.sidebar.checkbox("إظهار تفاصيل الذكاء الاصطناعي", value=False)

    st.sidebar.markdown("---")
    st.sidebar.caption("v2.0 - Production | صارم جداً")

    # --- Search Input ---
    query = st.text_input("ماذا تريد أن تتعلم اليوم؟", placeholder="مثال: بايثون، تسويق، إدارة أعمال...")

    # --- Logic ---
    if query:
        if len(query.strip()) < 2:
            st.warning("الرجاء كتابة كلمة بحث واضحة (حرفين على الأقل).")
            return

        with st.spinner("جاري التحليل والبحث..."):
            try:
                # Prepare Filter
                filters = {}
                if sel_category != "الكل": filters['category'] = sel_category
                if sel_level != "الكل": filters['level'] = sel_level

                request = RecommendRequest(
                    query=query,
                    top_k=top_k,
                    filters=filters,
                    rerank=enable_rerank
                )
                
                # Run Pipeline
                response = pipeline.recommend(request)

                # --- Display Results ---
                if response.total_found == 0:
                    st.warning("⚠️ لم يتم العثور على أي كورسات تطابق بحثك بدقة.")
                    st.info("نصيحة: جرب كلمات عامة أكثر، أو تأكد من الإملاء. نظامنا صارم ويعرض فقط الكورسات ذات الصلة المباشرة.")
                else:
                    st.success(f"تم العثور على {response.total_found} كورس مناسب!")
                    
                    for res in response.results:
                        # Translate Level/Category visual if needed, currently passing English data
                        # We can improve this if we had Arabic mappings for data too.
                        
                        why_html = ""
                        if show_debug and res.match_reasons:
                            reasons = " • ".join(res.match_reasons)
                            kws = ", ".join(res.matched_keywords)
                            why_html = f"""
                            <div class='why-section'>
                                <strong>💡 لماذا هذا الكورس؟</strong><br>
                                الأسباب: {reasons}<br>
                                الكلمات المطابقة: {kws}
                            </div>
                            """
                        
                        card_html = f"""
                        <div class="course-card">
                            <a href="{res.url}" target="_blank" class="course-title">
                                #{res.rank} {res.title}
                            </a>
                            <div class="course-meta">
                                <span class="score-badge">الصلة: {int(res.score * 100)}%</span>
                                | التصنيف: {res.category} | المستوى: {res.level}
                            </div>
                            <div class="course-desc">
                                {res.debug_info.get('desc_snippet', '')}...
                            </div>
                            {why_html}
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                    if show_debug:
                        with st.expander("🛠️ البيانات التقنية الكاملة (JSON)"):
                            st.json(response.dict())

            except Exception as e:
                st.error(f"حدث خطأ غير متوقع: {e}")
                # st.exception(e) # Uncomment for dev trace

if __name__ == "__main__":
    main()
