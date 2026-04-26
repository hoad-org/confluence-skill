"""Command-line interface for Confluence Skill.

This module provides the CLI entry point for the confluence command,
allowing users to invoke Confluence operations from the terminal.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from confluence_skill.skill import ConfluenceSkill
from confluence_skill.models import SkillConfig
from confluence_skill._version import __version__

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_config() -> SkillConfig:
    """Load configuration from .confluence.yaml or environment variables."""
    try:
        return SkillConfig.from_yaml(".confluence.yaml")
    except FileNotFoundError:
        return SkillConfig.from_env()


def cmd_document(args: argparse.Namespace) -> int:
    """Handle 'document' subcommand."""
    try:
        config = get_config()
        skill = ConfluenceSkill(config)

        result = skill.document(
            task=args.task,
            doc_type=args.doc_type,
            repo_path=args.repo_path,
            dry_run=args.dry_run,
        )

        print(result.summary)
        return 0
    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Handle 'search' subcommand."""
    try:
        config = get_config()
        skill = ConfluenceSkill(config)

        pages = skill.search_pages(
            query=args.query,
            space_key=args.space_key,
        )

        if pages:
            print(f"Found {len(pages)} pages:")
            for page in pages[:args.max_results]:
                title = page.get("title", "Untitled")
                page_id = page.get("id", "unknown")
                url = page.get("_links", {}).get("webui", "")
                print(f"  - {title} (ID: {page_id})")
                if url:
                    print(f"    {url}")
        else:
            print("No pages found.")
        return 0
    except Exception as e:
        logger.error(f"Error searching pages: {e}")
        return 1


def cmd_archive(args: argparse.Namespace) -> int:
    """Handle 'archive' subcommand."""
    try:
        config = get_config()
        skill = ConfluenceSkill(config)

        skill.archive_page(page_id=args.page_id)
        print(f"Successfully archived page {args.page_id}")
        return 0
    except Exception as e:
        logger.error(f"Error archiving page: {e}")
        return 1


def cmd_help_mcp(args: argparse.Namespace) -> int:
    """Show MCP server help information."""
    print("""
Confluence Skill MCP Server
===========================

This skill is available as an MCP (Model Context Protocol) server for Claude.

Configuration in ~/.claude/settings.json:
{
  "mcpServers": {
    "confluence": {
      "command": "python3",
      "args": ["-m", "confluence_skill.mcp"],
      "cwd": "/path/to/confluence-skill"
    }
  }
}

In Claude, use:
  /confluence document "Generate API docs" doc_type=api dry_run=true
  /confluence search "payment API"
  /confluence archive page_id=123456

Environment Variables:
  CONFLUENCE_TOKEN  - API token (required)
  JIRA_TOKEN       - Jira API token (optional, for Jira integration)

Configuration File:
  ~/.confluence.yaml - Optional configuration file for default space, instance URL, etc.

For more information:
  confluence --help
  confluence <command> --help
""")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"Confluence Skill {__version__}")
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enterprise-grade Confluence Cloud documentation skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  confluence document "Document the payment API" doc_type=api dry_run=true
  confluence search "payment API" space_key=ENGINEERING max_results=10
  confluence archive page_id=123456 reason="Obsolete"

For more information, visit: https://github.com/rhyscraig/confluence-skill
""",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Document subcommand
    doc_parser = subparsers.add_parser("document", help="Generate documentation")
    doc_parser.add_argument("task", help="Documentation task")
    doc_parser.add_argument(
        "--doc-type", "-t",
        dest="doc_type",
        choices=["api", "architecture", "adr", "runbook", "feature", "infrastructure", "troubleshooting", "custom"],
        required=True,
        help="Type of documentation",
    )
    doc_parser.add_argument(
        "--repo-path", "-r",
        dest="repo_path",
        default=".",
        help="Repository path (default: .)",
    )
    doc_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Preview only, don't publish (default: true)",
    )
    doc_parser.add_argument(
        "--publish",
        dest="dry_run",
        action="store_false",
        help="Publish to Confluence",
    )
    doc_parser.set_defaults(func=cmd_document)

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search for pages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--space-key", "-s",
        dest="space_key",
        default=None,
        help="Confluence space key (optional)",
    )
    search_parser.add_argument(
        "--max-results", "-m",
        dest="max_results",
        type=int,
        default=10,
        help="Maximum results to return (default: 10)",
    )
    search_parser.set_defaults(func=cmd_search)

    # Archive subcommand
    archive_parser = subparsers.add_parser("archive", help="Archive a page")
    archive_parser.add_argument("page_id", help="Page ID to archive")
    archive_parser.add_argument(
        "--reason",
        default="Archived by automation",
        help="Reason for archival",
    )
    archive_parser.set_defaults(func=cmd_archive)

    # Help for MCP
    help_parser = subparsers.add_parser("mcp-help", help="Show MCP server help")
    help_parser.set_defaults(func=cmd_help_mcp)

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Handle version flag
    if args.version:
        return cmd_version(args)

    # Handle subcommands
    if hasattr(args, "func"):
        return args.func(args)

    # Show help if no command provided
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
