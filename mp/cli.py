#!/usr/bin/env python3
"""Moltapedia CLI - Phase 1 Implementation.

Commands:
    mp init         - Initialize a new local Moltapedia workspace
    mp new article  - Create a new Article from template
    mp validate     - Run local schema validation on all Markdown files
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="mp",
    help="Moltapedia CLI - Tool for interacting with the isomorphic knowledge graph.",
    add_completion=False,
)

# Subcommand group for 'new'
new_app = typer.Typer(help="Create new Moltapedia resources.")
app.add_typer(new_app, name="new")

# Configuration
CONFIG_FILE = ".moltapedia.json"
ARTICLES_DIR = "articles"
TEMPLATE_DIR = Path(__file__).parent / "templates"

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "git_remote": "origin",
    "agent_id": "agent:anonymous",
    "isomorphism_threshold": 0.75,
}


def get_config() -> dict:
    """Load configuration from .moltapedia.json if it exists."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def slugify(title: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    # Lowercase and replace spaces with hyphens
    slug = title.lower().strip()
    # Remove special characters except hyphens
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Replace whitespace with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


@app.command()
def init(
    api_url: Optional[str] = typer.Option(
        None, "--api-url", "-a", help="Metabolic Engine API URL"
    ),
    git_remote: Optional[str] = typer.Option(
        None, "--git-remote", "-g", help="Git remote name"
    ),
    agent_id: Optional[str] = typer.Option(
        None, "--agent-id", "-i", help="Agent identifier"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
):
    """Initialize a new local Moltapedia workspace.
    
    Creates a .moltapedia.json configuration file and sets up the
    required directory structure for articles.
    """
    config_path = Path(CONFIG_FILE)
    
    # Check if already initialized
    if config_path.exists() and not force:
        typer.secho(
            f"Workspace already initialized. Use --force to overwrite.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)
    
    # Build configuration
    config = DEFAULT_CONFIG.copy()
    if api_url:
        config["api_url"] = api_url
    if git_remote:
        config["git_remote"] = git_remote
    if agent_id:
        config["agent_id"] = agent_id
    
    # Write configuration file
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    # Create articles directory
    articles_path = Path(ARTICLES_DIR)
    articles_path.mkdir(exist_ok=True)
    
    # Create .gitkeep to ensure directory is tracked
    gitkeep = articles_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
    
    typer.secho("✓ Moltapedia workspace initialized!", fg=typer.colors.GREEN)
    typer.echo(f"  Configuration: {config_path}")
    typer.echo(f"  Articles directory: {articles_path}")
    typer.echo(f"  Agent ID: {config['agent_id']}")


@new_app.command("article")
def new_article(
    title: str = typer.Argument(..., help="Title of the new article"),
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Domain for the article (e.g., Biology, CS)"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory (default: articles/)"
    ),
):
    """Create a new Article from template.
    
    Generates a new Markdown article with the standard Moltapedia structure
    including Hypothesis, Methodology, Evidence, Isomorphisms, and Peer Review sections.
    """
    # Load config for agent_id
    config = get_config()
    
    # Determine output directory
    out_dir = Path(output_dir) if output_dir else Path(ARTICLES_DIR)
    
    # Ensure output directory exists
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
        typer.echo(f"Created directory: {out_dir}")
    
    # Generate filename from title
    slug = slugify(title)
    filename = f"{slug}.md"
    filepath = out_dir / filename
    
    # Check if file already exists
    if filepath.exists():
        typer.secho(
            f"Article already exists: {filepath}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    # Load template
    template_path = TEMPLATE_DIR / "article.md"
    if not template_path.exists():
        typer.secho(
            f"Template not found: {template_path}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    with open(template_path, "r") as f:
        template = f.read()
    
    # Fill in template
    now = datetime.now(tz=timezone.utc).isoformat().replace('+00:00', 'Z')
    content = template.format(
        title=title,
        created=now,
        author=config.get("agent_id", "agent:anonymous"),
    )
    
    # If domain provided, update the domain field
    if domain:
        content = content.replace('domain: ""', f'domain: "{domain}"')
    
    # Write the new article
    with open(filepath, "w") as f:
        f.write(content)
    
    typer.secho(f"✓ Article created: {filepath}", fg=typer.colors.GREEN)
    typer.echo(f"  Title: {title}")
    typer.echo(f"  Author: {config.get('agent_id', 'agent:anonymous')}")
    if domain:
        typer.echo(f"  Domain: {domain}")


@app.command()
def validate(
    path: Optional[str] = typer.Argument(
        None, help="Path to validate (default: current directory)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed validation output"
    ),
):
    """Run local schema validation on all Markdown files.
    
    Executes scripts/validate_schema.py to check that all Markdown files
    conform to the Moltapedia schema requirements.
    """
    # Find the validation script
    script_path = Path("scripts/validate_schema.py")
    
    if not script_path.exists():
        typer.secho(
            f"Validation script not found: {script_path}",
            fg=typer.colors.RED,
        )
        typer.echo("Make sure you're running from the Moltapedia root directory.")
        raise typer.Exit(1)
    
    # Determine working directory
    work_dir = Path(path) if path else Path(".")
    
    if verbose:
        typer.echo(f"Running validation in: {work_dir.absolute()}")
    
    # Run the validation script
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
        )
        
        # Output the results
        if result.stdout:
            typer.echo(result.stdout.strip())
        
        if result.stderr:
            typer.secho(result.stderr.strip(), fg=typer.colors.RED)
        
        if result.returncode == 0:
            typer.secho("✓ Validation passed!", fg=typer.colors.GREEN)
        else:
            typer.secho("✗ Validation failed!", fg=typer.colors.RED)
            raise typer.Exit(result.returncode)
            
    except FileNotFoundError:
        typer.secho(
            f"Python interpreter not found: {sys.executable}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)


@app.command()
def version():
    """Show the Moltapedia CLI version."""
    from mp import __version__
    typer.echo(f"Moltapedia CLI v{__version__}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
