from src.recommender import CourseRecommender
import os
import shutil

# Clean outputs first to verify creation
if os.path.exists("outputs"):
    for f in os.listdir("outputs"):
        os.remove(os.path.join("outputs", f))

rec = CourseRecommender()
rec.load_courses("data/courses.csv")

print(f"Dataset Hash: {rec.dataset_hash}")
print(f"Abbr Map: {rec.abbr_map}")

expected_file = f"outputs/embeddings_{rec.dataset_hash}.npy"
if os.path.exists(expected_file):
    print("SUCCESS: Embeddings file created.")
else:
    print("FAILURE: Embeddings file not found.")

# Check expansion
# "NLP" in skills should be in map
if "nlp" in rec.abbr_map:
    print(f"NLP mapped to: {rec.abbr_map['nlp']}")
else:
    print("NLP not in abbr map (check logic).")

res = rec.recommend("nlp")
print(f"Query expansion debug: {res['debug_info']['expanded_query']}")
