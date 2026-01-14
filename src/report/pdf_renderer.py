import asyncio
from jinja2 import Environment, FileSystemLoader, Template
from playwright.async_api import async_playwright
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Inline CSS for the dashboard
DASHBOARD_CSS = """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #333;
    line-height: 1.6;
    margin: 0;
    padding: 40px;
    background-color: #f4f7f6;
}
.report-container {
    max-width: 1000px;
    margin: 0 auto;
    background: white;
    padding: 40px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-radius: 8px;
}
.header {
    border-bottom: 2px solid #0056b3;
    margin-bottom: 30px;
    padding-bottom: 10px;
}
.header h1 {
    margin: 0;
    color: #0056b3;
    font-size: 28px;
}
.header .date {
    font-size: 14px;
    color: #666;
}
.kpi-container {
    display: flex;
    justify-content: space-between;
    margin-bottom: 40px;
    gap: 20px;
}
.kpi-card {
    flex: 1;
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #e9ecef;
}
.kpi-card h3 {
    margin: 0;
    font-size: 14px;
    color: #666;
    text-transform: uppercase;
}
.kpi-card .value {
    font-size: 32px;
    font-weight: bold;
    color: #0056b3;
    margin: 10px 0 0;
}
.section {
    margin-bottom: 40px;
}
.section h2 {
    font-size: 20px;
    color: #333;
    border-left: 4px solid #0056b3;
    padding-left: 10px;
    margin-bottom: 20px;
}
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    text-align: left;
    padding: 12px;
    border-bottom: 1px solid #eee;
}
th {
    background: #f8f9fa;
    color: #666;
    font-weight: 600;
}
.chart-grid {
    display: flex;
    gap: 30px;
    margin-bottom: 40px;
}
.chart-item {
    flex: 1;
}
.chart-container {
    background: #fff;
    padding: 20px;
    text-align: center;
}
.footer {
    text-align: center;
    font-size: 12px;
    color: #999;
    margin-top: 50px;
    border-top: 1px solid #eee;
    padding-top: 20px;
}
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weekly Catalogue Intelligence Report</title>
    <style>
        {{ css }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>Weekly Catalogue Intelligence Report</h1>
            <div class="date">Generated on: {{ generated_at }}</div>
        </div>

        <div class="kpi-container">
            <div class="kpi-card">
                <h3>Total Courses</h3>
                <div class="value">{{ kpis.total_courses }}</div>
            </div>
            <div class="kpi-card">
                <h3>Unique Categories</h3>
                <div class="value">{{ kpis.total_categories }}</div>
            </div>
            <div class="kpi-card">
                <h3>Active Instructors</h3>
                <div class="value">{{ kpis.total_instructors }}</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-item">
                <div class="section">
                    <h2>Category Distribution</h2>
                    <div class="chart-container">
                        {{ category_chart_svg }}
                    </div>
                </div>
            </div>
            <div class="chart-item">
                <div class="section">
                    <h2>Level Distribution</h2>
                    <div class="chart-container">
                        {{ level_chart_svg }}
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Top {{ top_categories|length }} Categories</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category Name</th>
                        <th>Course Count</th>
                        <th>Share</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cat in top_categories %}
                    <tr>
                        <td>{{ cat.name }}</td>
                        <td>{{ cat.course_count }}</td>
                        <td>{{ (cat.share * 100)|round(1) }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Insights</h2>
            <ul>
                {% for insight in insights %}
                <li>{{ insight }}</li>
                {% endfor %}
            </ul>
        </div>

        <div class="footer">
            Generated automatically by n8n + Zedny Report API
        </div>
    </div>
</body>
</html>
"""

def generate_bar_chart_svg(labels, values, title=""):
    """Generates an inline SVG bar chart."""
    if not values: return ""
    max_val = max(values)
    width = 400
    height = 250
    bar_width = 30
    gap = 15
    chart_h = height - 50
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    for i, (label, val) in enumerate(zip(labels, values)):
        bh = (val / max_val) * chart_h if max_val > 0 else 0
        x = 50 + i * (bar_width + gap)
        y = chart_h - bh + 20
        svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bh}" fill="#0056b3" />'
        # Label (truncated)
        short_label = label[:6] + ".." if len(label) > 8 else label
        svg += f'<text x="{x + bar_width/2}" y="{chart_h + 35}" font-size="10" text-anchor="middle" fill="#666">{short_label}</text>'
        # Value
        svg += f'<text x="{x + bar_width/2}" y="{y - 5}" font-size="10" text-anchor="middle" font-weight="bold" fill="#333">{val}</text>'
    svg += '</svg>'
    return svg

def generate_donut_chart_svg(labels, values):
    """Generates an inline SVG donut chart."""
    if not values: return ""
    total = sum(values)
    width = 250
    height = 250
    center = 125
    radius = 80
    inner_radius = 50
    
    import math
    
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    current_angle = 0
    colors = ["#0056b3", "#28a745", "#ffc107", "#dc3545", "#17a2b8"]
    
    for i, (label, val) in enumerate(zip(labels, values)):
        if total == 0: continue
        percent = val / total
        slice_angle = percent * 2 * math.pi
        
        # Draw path
        x1 = center + radius * math.cos(current_angle)
        y1 = center + radius * math.sin(current_angle)
        x2 = center + radius * math.cos(current_angle + slice_angle)
        y2 = center + radius * math.sin(current_angle + slice_angle)
        
        large_arc = 1 if slice_angle > math.pi else 0
        
        svg += f'<path d="M {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2}" fill="none" stroke="{colors[i % len(colors)]}" stroke-width="{radius-inner_radius}" />'
        
        # Legend (simplified)
        lx = 10
        ly = 20 + i * 15
        svg += f'<rect x="{lx}" y="{ly}" width="10" height="10" fill="{colors[i % len(colors)]}" />'
        svg += f'<text x="{lx + 15}" y="{ly + 9}" font-size="9" fill="#666">{label} ({int(percent*100)}%)</text>'
        
        current_angle += slice_angle
        
    svg += f'<circle cx="{center}" cy="{center}" r="{inner_radius}" fill="white" />'
    svg += '</svg>'
    return svg

def render_catalog_weekly_html(report: dict) -> str:
    """Renders the executive HTML dashboard."""
    env = Environment()
    template = env.from_string(HTML_TEMPLATE)
    
    # Prepare chart data
    chart_data = report.get("chart_data", {})
    cat_labels = chart_data.get("categories_labels", [])[:8]
    cat_values = chart_data.get("categories_values", [])[:8]
    
    lvl_labels = chart_data.get("levels_labels", [])
    lvl_values = chart_data.get("levels_values", [])
    
    cat_svg = generate_bar_chart_svg(cat_labels, cat_values)
    lvl_svg = generate_donut_chart_svg(lvl_labels, lvl_values)
    
    # Handle generated_at format
    gen_at = report.get("generated_at", "")
    try:
        dt = datetime.fromisoformat(gen_at.replace("Z", "+00:00"))
        gen_at_readable = dt.strftime("%B %d, %Y - %I:%M %p UTC")
    except:
        gen_at_readable = gen_at
        
    html_out = template.render(
        css=DASHBOARD_CSS,
        generated_at=gen_at_readable,
        kpis=report.get("kpis", {}),
        top_categories=report.get("top_categories", []),
        insights=report.get("insights", []),
        category_chart_svg=cat_svg,
        level_chart_svg=lvl_svg
    )
    return html_out

async def html_to_pdf(html: str) -> bytes:
    """Converts HTML string to PDF bytes using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set content directly
        await page.set_content(html, wait_until="networkidle")
        
        # Generate PDF
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"}
        )
        await browser.close()
        return pdf_bytes
