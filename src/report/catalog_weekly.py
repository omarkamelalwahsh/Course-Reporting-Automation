import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.scraper.client import ZednyClient, ZednyClientError

logger = logging.getLogger(__name__)

def build_catalog_weekly_report(top_n: int = 10, bottom_n: int = 10) -> Dict[str, Any]:
    """
    Builds a professional Weekly Catalogue Intelligence Report.
    """
    logger.info(f"Starting build_catalog_weekly_report(top_n={top_n}, bottom_n={bottom_n})")
    client = ZednyClient()
    
    try:
        courses = client.get_all_courses()
    except ZednyClientError as e:
        logger.error(f"Report generation aborted: Zedny API error: {e}")
        raise

    total_courses = len(courses)
    if total_courses == 0:
        return _empty_report()

    # Data transformation & aggregation
    categories_map = {}
    instructors_map = {}
    levels_map = {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "Unknown": 0}

    for course in courses:
        # Levels
        lvl = course.get("level", "Unknown")
        if lvl not in levels_map:
            lvl = "Unknown"
        levels_map[lvl] += 1

        # Categories
        for cat in course.get("categories", []) or []:
            if not cat: continue  # Guard against None in list
            cat_id = cat.get("id")
            if cat_id:
                if cat_id not in categories_map:
                    categories_map[cat_id] = {"name": cat.get("name", "Unknown"), "count": 0}
                categories_map[cat_id]["count"] += 1

        # Instructors
        for inst in course.get("instructors", []) or []:
            if not inst: continue  # Guard against None in list
            inst_id = inst.get("id")
            if inst_id:
                if inst_id not in instructors_map:
                    instructors_map[inst_id] = {"name": inst.get("name", "Unknown"), "count": 0}
                instructors_map[inst_id]["count"] += 1

    # Format Results
    # Levels distribution
    levels_dist = [
        {"level": k, "count": v, "share": round(v / total_courses, 4)}
        for k, v in levels_map.items() if v > 0
    ]
    levels_dist.sort(key=lambda x: x["count"], reverse=True)

    # Categories stats
    all_cat_stats = [
        {"id": k, "name": v["name"], "course_count": v["count"], "share": round(v["count"] / total_courses, 4)}
        for k, v in categories_map.items()
    ]
    all_cat_stats.sort(key=lambda x: x["course_count"], reverse=True)

    top_categories = all_cat_stats[:top_n]
    low_coverage_categories = all_cat_stats[-bottom_n:] if len(all_cat_stats) > bottom_n else all_cat_stats
    low_coverage_categories.sort(key=lambda x: x["course_count"]) # Ascending for "low coverage"

    # Instructor stats
    all_inst_stats = [
        {"id": k, "name": v["name"], "course_count": v["count"]}
        for k, v in instructors_map.items()
    ]
    all_inst_stats.sort(key=lambda x: x["course_count"], reverse=True)
    top_instructors = all_inst_stats[:10]

    # Insights
    insights = []
    if all_cat_stats:
        highest_cat = all_cat_stats[0]
        insights.append(f"The highest category is '{highest_cat['name']}' with {highest_cat['course_count']} courses.")
        
        lowest_cat = all_cat_stats[-1]
        insights.append(f"The category with lowest coverage is '{lowest_cat['name']}' with {lowest_cat['course_count']} courses.")
    
    if top_instructors:
        top_inst = top_instructors[0]
        insights.append(f"Top instructor is {top_inst['name']} contributing to {top_inst['course_count']} courses.")

    # Concentration (Top 3 share)
    top_3_count = sum(c["course_count"] for c in all_cat_stats[:3])
    conc_share = round((top_3_count / total_courses) * 100, 2)
    insights.append(f"Top 3 categories represent {conc_share}% of the total catalogue (High concentration)." if conc_share > 50 else f"Catalogue is well-balanced with top 3 categories representing {conc_share}%.")

    dominating_level = levels_dist[0]["level"] if levels_dist else "any"
    insights.append(f"Catalogue is primarily composed of {dominating_level} level courses.")

    # Markdown Summary
    markdown = _generate_markdown(total_courses, len(categories_map), len(instructors_map), top_categories, low_coverage_categories, levels_dist)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "zedny_api",
        "kpis": {
            "total_courses": total_courses,
            "total_categories": len(categories_map),
            "total_instructors": len(instructors_map)
        },
        "levels_distribution": levels_dist,
        "categories": all_cat_stats,
        "top_categories": top_categories,
        "low_coverage_categories": low_coverage_categories,
        "top_instructors": top_instructors,
        "featured": [],
        "top_sliders": [],
        "insights": insights,
        "markdown_summary": markdown,
        "chart_data": {
            "categories_labels": [c["name"] for c in top_categories],
            "categories_values": [c["course_count"] for c in top_categories],
            "levels_labels": [l["level"] for l in levels_dist],
            "levels_values": [l["count"] for l in levels_dist]
        }
    }

    return report

def _generate_markdown(total, cats, insts, top_cats, bottom_cats, levels) -> str:
    md = f"""# Weekly Catalogue Intelligence Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Key Performance Indicators
- **Total Courses**: {total}
- **Unique Categories**: {cats}
- **Active Instructors**: {insts}

## 🏆 Top 5 Categories
"""
    for cat in top_cats[:5]:
        md += f"- **{cat['name']}**: {cat['course_count']} courses ({cat['share']*100:.1f}% share)\n"

    md += "\n## 🔻 Bottom 5 Categories (Low Coverage)\n"
    for cat in bottom_cats[:5]:
        md += f"- **{cat['name']}**: {cat['course_count']} courses\n"

    md += "\n## 📚 Levels Distribution\n"
    for lvl in levels:
        md += f"- **{lvl['level']}**: {lvl['count']} courses ({lvl['share']*100:.1f}%)\n"

    md += """
## 💡 Suggested Actions
- **Expand Content**: Focus on growing the bottom categories to provide more variety.
- **Leverage Experts**: Collaborate further with top instructors to create series or bundles.
- **Level Balancing**: Evaluate if the current distribution of levels matches the target user personas.
"""
    return md

def _empty_report() -> Dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "empty",
        "message": "No course data found."
    }
