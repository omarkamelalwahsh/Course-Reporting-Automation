import re

# Stopwords List (English + Arabic)
STOPWORDS = {
    'the', 'is', 'in', 'for', 'where', 'when', 'to', 'at', 'be', 'this', 'that',
    'how', 'what', 'a', 'an', 'of', 'and', 'or', 'with', 'by', 'from',
    'need', 'looking', 'for', 'in', 'on', 'of', 'and', 'with', 'please', 'pls',
    'programming', 'language', 'انا', 'عاوز', 'عايز', 'محتاج', 'اتعلم', 'كورس', 
    'شرح', 'من', 'فضلك', 'في', 'على', 'عن'
}

def is_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return bool(re.search(r'[\u0600-\u06FF]', text))

def normalize_query(query: str) -> str:
    """
    Normalize query: lowercase, remove punctuation, remove extra spaces.
    Expand common abbreviations: ML, NLP, AWS, BI, CV.
    Remove stopwords.
    """
    # 1. Lowercase
    q = query.lower()
    
    # 2. Translate Common Arabic Tech Terms to English
    # This is critical for zero-shot multilingual support on English-heavy datasets
    ar_to_en = {
        'بايثون': 'python', 'جافا': 'java', 'بيانات': 'data', 'برمجة': 'programming',
        'تصميم': 'design', 'مواقع': 'web', 'ذكاء': 'intelligence', 'اصطناعي': 'artificial',
        'تعلم': 'learning', 'الالة': 'machine', 'الآلة': 'machine', 'شبكات': 'networks',
        'أمن': 'security', 'سيبراين': 'cyber', 'كورس': 'course', 'دورة': 'course',
        'تحليل': 'analysis', 'فلاتر': 'flutter', 'رياكت': 'react', 'اكسل': 'excel',
        'وورد': 'word', 'باوربوينت': 'powerpoint', 'تسويق': 'marketing', 'إدارة': 'management'
    }
    for ar, en in ar_to_en.items():
        q = q.replace(ar, en) # Simple string replacement is safer than regex for mixed scripts
    
    # 3. Expand common abbreviations
    abbr_map = {
        'ml': 'machine learning',
        'nlp': 'natural language processing',
        'aws': 'amazon web services',
        'bi': 'business intelligence',
        'cv': 'computer vision'
    }
    for abbr, full in abbr_map.items():
        pattern = re.compile(r'\b' + re.escape(abbr) + r'\b')
        q = pattern.sub(full, q)
        
    # 3. Remove Punctuation
    q = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', q)
    
    # 4. Remove Stopwords & extra spaces
    tokens = q.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    
    return " ".join(tokens).strip()
