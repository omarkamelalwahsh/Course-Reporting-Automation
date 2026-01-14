import sys
import argparse
import logging
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__)

def check_environment():
    """Validates that all required environment variables are present."""
    logger.info("Performing environment validation...")
    missing = settings.check_env()
    if missing:
        logger.critical(f"Missing required environment variables: {', '.join(missing)}")
        print(f"\nERROR: Missing environment variables: {', '.join(missing)}")
        print("Please copy .env.example to .env and fill in the required values.")
        sys.exit(1)
    logger.info("Environment validation successful.")

def cmd_scrape(args):
    """Handler for the 'scrape' command."""
    from src.scraper.client import ZednyClient
    logger.info("Starting course scraping...")
    client = ZednyClient()
    courses = client.get_all_courses(limit=args.limit)
    print(f"Successfully scraped {len(courses)} courses.")

def cmd_report(args):
    """Handler for the 'report' command."""
    from src.report.catalog_weekly import build_catalog_weekly_report
    logger.info("Generating weekly catalog report...")
    report = build_catalog_weekly_report()
    print("Report generated successfully.")
    if args.output:
        # Logic to save report to file could go here
        print(f"Report summary: Total courses count: {report['kpis']['total_courses']}")

def cmd_search(args):
    """Handler for the 'search' command."""
    from src.ai.pipeline import CourseRecommenderPipeline
    from src.schemas import RecommendRequest
    
    logger.info(f"Performing AI search for: {args.query}")
    pipeline = CourseRecommenderPipeline()
    request = RecommendRequest(query=args.query, top_k=args.top_k)
    response = pipeline.recommend(request)
    
    print(f"\nFound {len(response.results)} matches:")
    for i, res in enumerate(response.results):
        print(f"{i+1}. {res.title} [{res.rank}/10] - {res.url}")

def main():
    parser = argparse.ArgumentParser(description="Zedny Course Intelligence System - CLI Entrypoint")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scrape command
    p_scrape = subparsers.add_parser("scrape", help="Scrape courses from API")
    p_scrape.add_argument("--limit", type=int, default=50, help="Max courses to fetch")

    # Report command
    p_report = subparsers.add_parser("report", help="Generate weekly intelligence report")
    p_report.add_argument("--output", action="store_true", help="Save report to outputs folder")

    # Search command
    p_search = subparsers.add_parser("search", help="Semantic course search")
    p_search.add_argument("query", type=str, help="Search query")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Always check environment before running any business logic
    check_environment()

    try:
        if args.command == "scrape":
            cmd_scrape(args)
        elif args.command == "report":
            cmd_report(args)
        elif args.command == "search":
            cmd_search(args)
    except Exception as e:
        logger.exception(f"Command '{args.command}' failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
