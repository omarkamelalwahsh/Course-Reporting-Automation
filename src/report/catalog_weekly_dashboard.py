import io
import matplotlib.pyplot as plt
from datetime import datetime

def build_weekly_bi_dashboard(report: dict) -> bytes:
    """
    Takes full report dict and returns a BI-style dashboard PNG (bytes).
    """

    # ---- KPI Values ----
    kpis = report["kpis"]
    total_courses = kpis["total_courses"]
    total_categories = kpis["total_categories"]
    total_instructors = kpis["total_instructors"]

    generated_at = report.get("generated_at", datetime.utcnow().isoformat())

    # ---- Chart Data ----
    chart_data = report["chart_data"]

    categories_labels = chart_data["categories_labels"]
    categories_values = chart_data["categories_values"]

    levels_labels = chart_data["levels_labels"]
    levels_values = chart_data["levels_values"]

    # ---- Figure Setup ----
    fig = plt.figure(figsize=(14, 8), dpi=180)
    fig.patch.set_facecolor("white")

    # Grid layout
    ax_title = plt.subplot2grid((6, 6), (0, 0), colspan=6)
    ax_kpi1 = plt.subplot2grid((6, 6), (1, 0), colspan=2)
    ax_kpi2 = plt.subplot2grid((6, 6), (1, 2), colspan=2)
    ax_kpi3 = plt.subplot2grid((6, 6), (1, 4), colspan=2)

    ax_bar = plt.subplot2grid((6, 6), (2, 0), rowspan=4, colspan=4)
    ax_pie = plt.subplot2grid((6, 6), (2, 4), rowspan=2, colspan=2)
    ax_insights = plt.subplot2grid((6, 6), (4, 4), rowspan=2, colspan=2)

    # ---- Title ----
    ax_title.axis("off")
    ax_title.text(
        0.01, 0.65,
        "Weekly Catalogue Intelligence Dashboard",
        fontsize=20, fontweight="bold"
    )
    ax_title.text(
        0.01, 0.15,
        f"Generated on: {generated_at}",
        fontsize=11, alpha=0.7
    )

    # ---- KPI Cards Function ----
    def draw_kpi(ax, title, value):
        ax.set_facecolor("#f7f8fa")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.text(0.05, 0.65, title, fontsize=12, fontweight="bold", alpha=0.8)
        ax.text(0.05, 0.15, f"{value}", fontsize=24, fontweight="bold")

    draw_kpi(ax_kpi1, "Total Courses", total_courses)
    draw_kpi(ax_kpi2, "Unique Categories", total_categories)
    draw_kpi(ax_kpi3, "Active Instructors", total_instructors)

    # ---- Bar Chart: Top Categories ----
    ax_bar.set_facecolor("white")
    ax_bar.barh(categories_labels[::-1], categories_values[::-1])
    ax_bar.set_title("Top Categories (Courses Count)", fontsize=14, fontweight="bold")
    ax_bar.set_xlabel("Courses")
    ax_bar.grid(axis="x", linestyle="--", alpha=0.3)

    # ---- Pie Chart: Levels Distribution ----
    ax_pie.set_title("Levels Distribution", fontsize=14, fontweight="bold")
    ax_pie.pie(levels_values, labels=levels_labels, autopct="%1.1f%%")
    ax_pie.axis("equal")

    # ---- Insights Panel ----
    ax_insights.set_facecolor("#f7f8fa")
    ax_insights.set_xticks([])
    ax_insights.set_yticks([])
    for spine in ax_insights.spines.values():
        spine.set_visible(False)

    ax_insights.text(0.05, 0.9, "Insights", fontsize=14, fontweight="bold")

    insights = report.get("insights", [])
    for i, insight in enumerate(insights[:5]):
        ax_insights.text(0.05, 0.75 - (i * 0.14), f"• {insight}", fontsize=10, wrap=True)

    plt.tight_layout()

    # ---- Export to PNG bytes ----
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf.read()
