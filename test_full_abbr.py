from src.recommender import CourseRecommender
import pandas as pd
import os

# Create dummy CSV
data = {
    "title": ["Natural Language Processing (NLP)", "Machine Learning"],
    "category": ["AI", "AI"],
    "level": ["Advanced", "Beginner"],
    "description": ["Learn NLP basics.", "Intro to ML."],
    "skills": ["Text|Bert", "Python|Scikit"],
    "duration_hours": [10, 20]
}
df = pd.DataFrame(data)
df.to_csv("test_abbr.csv", index=False)

rec = CourseRecommender()
rec.load_courses("test_abbr.csv")

print(f"Abbr Map: {rec.abbr_map}")
if "nlp" in rec.abbr_map and "natural language processing" in rec.abbr_map["nlp"]:
    print("SUCCESS: Full Form extracted.")
else:
    print("FAILURE: Full Form NOT extracted.")

# Cleanup
os.remove("test_abbr.csv")
