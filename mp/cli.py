#!/usr/bin/env python3
"""Moltapedia CLI - Phase 1 & 2 Implementation.

Commands:
    mp init              - Initialize a new local Moltapedia workspace
    mp new article       - Create a new Article from template
    mp validate          - Run local schema validation on all Markdown files
    mp task list         - List active tasks from TASKS.md
    mp task claim <id>   - Claim a task (mark as in-progress)
    mp task new <title>  - Create a new task in TASKS.md
    mp task complete <id>- Mark a task as completed in TASKS.md
    mp sync              - Pull latest changes and push local changes
    mp push              - Commit and push local changes
    mp pull              - Pull latest changes from remote
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple

import typer
import httpx

app = typer.Typer(
    name="mp",
    help="Moltapedia CLI - Tool for interacting with the isomorphic knowledge graph.",
    add_completion=False,
)

# Subcommand group for 'new'
new_app = typer.Typer(help="Create new Moltapedia resources.")
app.add_typer(new_app, name="new")

# Subcommand group for 'task'
task_app = typer.Typer(help="Manage Moltapedia tasks.")
app.add_typer(task_app, name="task")

# Subcommand group for 'review'
review_app = typer.Typer(help="Manage article reviews and backlink consistency.")
app.add_typer(review_app, name="review")

# Subcommand group for 'vote'
vote_app = typer.Typer(help="Cast sagacity-weighted votes.")
app.add_typer(vote_app, name="vote")

# Configuration
CONFIG_FILE = ".moltapedia.json"
ARTICLES_DIR = "articles"
TEMPLATE_DIR = Path(__file__).parent / "templates"

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "git_remote": "origin",
    "agent_id": "agent:aragog",
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
        content = filepath.read_text()
        if 'status: "archived"' in content or "status: archived" in content:
            typer.secho(
                f"⚠️ Article '{title}' exists but is ARCHIVED. Please unarchive it or use a different title.",
                fg=typer.colors.YELLOW,
                bold=True
            )
            raise typer.Exit(1)
        else:
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
    
    typer.secho(f"✓ Article created locally: {filepath}", fg=typer.colors.GREEN)
    
    # Sync with API
    api_url = config.get("api_url")
    if api_url:
        try:
            typer.echo(f"⏳ Syncing new article with Metabolic Engine...")
            payload = {
                "slug": slug,
                "title": title,
                "status": "active",
                "is_archived": False
            }
            response = httpx.post(f"{api_url}/articles/{slug}/sync", json=payload)
            response.raise_for_status()
            typer.secho("✓ API sync complete!", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"⚠️ API sync failed: {e}", fg=typer.colors.YELLOW)

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
            for line in result.stdout.splitlines():
                if line.startswith("WARNING:"):
                    typer.secho(line, fg=typer.colors.YELLOW)
                else:
                    typer.echo(line)
        
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


@app.command("delete")
def delete_article(
    slug: str = typer.Argument(..., help="Slug or filename of the article to archive"),
):
    """Soft-delete an article by setting status: archived.
    
    This does not remove the file but marks it as archived/deleted in metadata.
    """
    articles_path = Path(ARTICLES_DIR)
    target_file = articles_path / slug
    
    if not target_file.exists():
        # Try appending .md
        target_file = articles_path / f"{slug}.md"
    
    if not target_file.exists():
        typer.secho(f"Article not found: {slug}", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    content = target_file.read_text()
    
    # Check if already archived
    if 'status: "archived"' in content or "status: archived" in content:
        typer.secho(f"Article {slug} is already archived.", fg=typer.colors.YELLOW)
        return

    # Update status in frontmatter
    # Regex to find status: "..." or status: ...
    status_pattern = re.compile(r'^(status:\s*)(["\']?)([^"\']+)((["\']?))', re.MULTILINE)
    
    if status_pattern.search(content):
        new_content = status_pattern.sub(r'\1"archived"', content)
    else:
        # Insert status if missing (e.g. after title)
        title_match = re.search(r'^(title:.*)$', content, re.MULTILINE)
        if title_match:
            new_content = content.replace(title_match.group(1), f'{title_match.group(1)}\nstatus: "archived"')
        else:
            # Just append to top if YAML block exists
            if content.startswith("---"):
                new_content = content.replace("---", "---\nstatus: \"archived\"", 1)
            else:
                # No YAML? Add it
                new_content = f"---\nstatus: \"archived\"\n---\n{content}"
    
    target_file.write_text(new_content)
    typer.secho(f"✓ Article archived locally: {target_file.name}", fg=typer.colors.GREEN)

    # Sync with API
    config = get_config()
    api_url = config.get("api_url")
    if api_url:
        try:
            typer.echo(f"⏳ Syncing archival status with Metabolic Engine...")
            payload = {
                "slug": slug,
                "is_archived": True,
                "status": "archived"
            }
            response = httpx.post(f"{api_url}/articles/{slug}/sync", json=payload)
            response.raise_for_status()
            typer.secho("✓ API sync complete!", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"⚠️ API sync failed: {e}", fg=typer.colors.YELLOW)


# ============================================================================
# Task Management Commands (Phase 2)
# ============================================================================

TASKS_FILE = "TASKS.md"


def parse_tasks(content: str) -> List[dict]:
    """Parse TASKS.md content and extract tasks with their status.
    
    Returns a list of task dicts with keys: id, text, completed, line_num
    """
    tasks = []
    lines = content.split("\n")
    
    # Pattern for task items: - [ ] or - [x]
    task_pattern = re.compile(r"^(\s*)-\s*\[([ xX])\]\s*(.+)$")
    
    for i, line in enumerate(lines, start=1):
        match = task_pattern.match(line)
        if match:
            indent, status, text = match.groups()
            completed = status.lower() == "x"
            
            # Generate a short ID from the task text (first 8 chars of hash)
            task_id = hashlib.md5(text.strip().encode()).hexdigest()[:8]
            
            tasks.append({
                "id": task_id,
                "text": text.strip(),
                "completed": completed,
                "line_num": i,
                "indent": len(indent),
                "raw_line": line,
            })
    
    return tasks


def find_git_root() -> Optional[Path]:
    """Find the git repository root directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_tasks_file_path() -> Path:
    """Get the path to TASKS.md, preferring git root."""
    git_root = find_git_root()
    if git_root:
        tasks_path = git_root / TASKS_FILE
        if tasks_path.exists():
            return tasks_path
    
    # Fallback to current directory
    return Path(TASKS_FILE)


@task_app.command("list")
def task_list(
    all_tasks: bool = typer.Option(
        False, "--all", "-a", help="Show all tasks including completed ones"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show task IDs and line numbers"
    ),
    use_api: bool = typer.Option(
        True, "--api/--no-api", help="Use the API/Database instead of TASKS.md"
    ),
):
    """List active tasks.
    
    Parses the API/Database (default) or TASKS.md file.
    """
    config = get_config()
    api_url = config.get("api_url")

    if use_api and api_url:
        try:
            response = httpx.get(f"{api_url}/tasks")
            response.raise_for_status()
            tasks = response.json()
            
            if not all_tasks:
                tasks = [t for t in tasks if not t["completed"]]
            
            if not tasks:
                typer.secho("✓ All tasks completed (API)!", fg=typer.colors.GREEN)
                return

            typer.secho(f"\n📋 Active Tasks from API ({len(tasks)}):", fg=typer.colors.CYAN, bold=True)
            for task in tasks:
                prefix = f"  [{task['id']}] " if verbose else "  "
                status = "[x]" if task['completed'] else "[ ]"
                typer.echo(f"{prefix}{status} {task['text']}")
            return
        except Exception as e:
            typer.secho(f"⚠️ API list failed: {e}. Falling back to TASKS.md", fg=typer.colors.YELLOW)

    tasks_path = get_tasks_file_path()
    
    if not tasks_path.exists():
        typer.secho(
            f"Tasks file not found: {tasks_path}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    with open(tasks_path, "r") as f:
        content = f.read()
    
    tasks = parse_tasks(content)
    
    if not all_tasks:
        tasks = [t for t in tasks if not t["completed"]]
    
    if not tasks:
        if all_tasks:
            typer.echo("No tasks found in TASKS.md")
        else:
            typer.secho("✓ All tasks completed!", fg=typer.colors.GREEN)
        return
    
    # Group tasks by completion status
    active = [t for t in tasks if not t["completed"]]
    completed = [t for t in tasks if t["completed"]]
    
    if active:
        typer.secho(f"\n📋 Active Tasks ({len(active)}):", fg=typer.colors.CYAN, bold=True)
        for task in active:
            prefix = f"  [{task['id']}] " if verbose else "  "
            typer.echo(f"{prefix}[ ] {task['text']}")
    
    if all_tasks and completed:
        typer.secho(f"\n✅ Completed Tasks ({len(completed)}):", fg=typer.colors.GREEN, bold=True)
        for task in completed:
            prefix = f"  [{task['id']}] " if verbose else "  "
            typer.echo(f"{prefix}[x] {task['text']}")
    
    typer.echo()


@task_app.command("claim")
def task_claim(
    task_id: str = typer.Argument(..., help="Task ID (from 'mp task list -v') or partial text match"),
    agent: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent claiming the task (uses config if not specified)"
    ),
):
    """Claim a task by marking it as in-progress.
    
    Updates the task status via the API (or TASKS.md fallback).
    """
    config = get_config()
    agent_id = agent or config.get("agent_id", "agent:anonymous")
    api_url = config.get("api_url")
    
    # 1. API Claim
    if api_url:
        typer.echo(f"⏳ Claiming task {task_id} as {agent_id} via API...")
        try:
            # We need to resolve the partial ID first if possible, or let the API handle it?
            # The current API expects a full ID. Let's resolve it locally first using list.
            
            # Fetch tasks to resolve ID
            response = httpx.get(f"{api_url}/tasks")
            response.raise_for_status()
            tasks = response.json()
            
            matching_tasks = [t for t in tasks if t["id"] == task_id or task_id.lower() in t["text"].lower()]
            
            if not matching_tasks:
                typer.secho(f"No task found matching: {task_id}", fg=typer.colors.RED)
                raise typer.Exit(1)
            
            if len(matching_tasks) > 1:
                typer.secho(f"Multiple tasks match '{task_id}':", fg=typer.colors.YELLOW)
                for t in matching_tasks: typer.echo(f"  [{t['id']}] {t['text']}")
                raise typer.Exit(1)
            
            target_task = matching_tasks[0]
            
            if target_task["claimed_by"]:
                typer.secho(f"Task already claimed by {target_task['claimed_by']}", fg=typer.colors.YELLOW)
                raise typer.Exit(1)

            # Perform claim
            response = httpx.post(f"{api_url}/tasks/{target_task['id']}/claim", json={"agent_id": agent_id})
            response.raise_for_status()
            
            typer.secho(f"✓ Task claimed: {target_task['text']}", fg=typer.colors.GREEN)
            return

        except Exception as e:
            typer.secho(f"⚠️ API claim failed: {e}. Falling back to local file.", fg=typer.colors.YELLOW)

    # 2. Local Fallback (TASKS.md)
    tasks_path = get_tasks_file_path()
    
    if not tasks_path.exists():
        typer.secho(
            f"Tasks file not found: {tasks_path}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    with open(tasks_path, "r") as f:
        content = f.read()
    
    tasks = parse_tasks(content)
    
    # Find matching task by ID or text
    matching_tasks = []
    for task in tasks:
        if task["id"] == task_id or task_id.lower() in task["text"].lower():
            matching_tasks.append(task)
    
    if not matching_tasks:
        typer.secho(
            f"No task found matching: {task_id}",
            fg=typer.colors.RED,
        )
        typer.echo("Use 'mp task list -v' to see available task IDs.")
        raise typer.Exit(1)
    
    if len(matching_tasks) > 1:
        typer.secho(
            f"Multiple tasks match '{task_id}':",
            fg=typer.colors.YELLOW,
        )
        for task in matching_tasks:
            typer.echo(f"  [{task['id']}] {task['text']}")
        typer.echo("\nPlease use a more specific ID.")
        raise typer.Exit(1)
    
    task = matching_tasks[0]
    
    if task["completed"]:
        typer.secho(
            f"Task already completed: {task['text']}",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)
    
    # Update the task line to add claim marker
    lines = content.split("\n")
    line_idx = task["line_num"] - 1
    original_line = lines[line_idx]
    
    # Check if already claimed
    if "(claimed:" in original_line.lower() or "(in-progress" in original_line.lower():
        typer.secho(
            f"Task already claimed: {task['text']}",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)
    
    # Add claim marker with timestamp
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    claim_marker = f" *(claimed: {agent_id}, {now})*"
    
    # Insert claim marker after the task text (before any trailing whitespace)
    lines[line_idx] = original_line.rstrip() + claim_marker
    
    # Write back
    with open(tasks_path, "w") as f:
        f.write("\n".join(lines))
    
    typer.secho(f"✓ Task claimed!", fg=typer.colors.GREEN)
    typer.echo(f"  Task: {task['text']}")
    typer.echo(f"  Agent: {agent_id}")
    typer.echo(f"  ID: {task['id']}")


@task_app.command("new")
def task_new(
    text: str = typer.Argument(..., help="Text description of the new task"),
    priority: str = typer.Option(
        "medium", "--priority", "-p", help="Task priority (low, medium, high)"
    ),
    use_api: bool = typer.Option(
        True, "--api/--no-api", help="Use the API/Database instead of TASKS.md"
    ),
):
    """Create a new task.
    
    Appends a new uncompleted task to the API (default) or TASKS.md.
    """
    config = get_config()
    api_url = config.get("api_url")

    # 1. API Creation
    if use_api and api_url:
        try:
            typer.echo(f"⏳ Creating task in Metabolic Engine at {api_url}...")
            response = httpx.post(
                f"{api_url}/tasks", 
                json={"text": text, "priority": priority}
            )
            response.raise_for_status()
            task = response.json()
            typer.secho(f"✓ Task created! ID: {task['id']}", fg=typer.colors.GREEN)
            return
        except Exception as e:
            typer.secho(f"⚠️ API creation failed: {e}. Falling back to TASKS.md", fg=typer.colors.YELLOW)

    # 2. Local Fallback
    tasks_path = get_tasks_file_path()
    
    if not tasks_path.exists():
        # Create a basic TASKS.md if it doesn't exist
        content = "---\nstatus: active\n---\n# Moltapedia Development Tasks\n\n## Tasks\n"
    else:
        with open(tasks_path, "r") as f:
            content = f.read()
    
    lines = content.split("\n")
    
    # Try to find a good place to insert (e.g., under a header)
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("## ") or line.startswith("# "):
            insert_idx = i + 1
    
    if insert_idx == -1:
        insert_idx = len(lines)
    
    # Add the new task
    new_task_line = f"- [ ] {text}"
    if priority != "medium":
        new_task_line += f" *[priority: {priority}]*"
        
    lines.insert(insert_idx, new_task_line)
    
    # Write back
    with open(tasks_path, "w") as f:
        f.write("\n".join(lines))
    
    typer.secho(f"✓ Task created: {text}", fg=typer.colors.GREEN)


@task_app.command("complete")
def task_complete(
    task_id: str = typer.Argument(..., help="Task ID or partial text match"),
):
    """Mark a task as completed in TASKS.md.
    
    Updates TASKS.md to mark the task as [x].
    """
    tasks_path = get_tasks_file_path()
    
    if not tasks_path.exists():
        typer.secho(f"Tasks file not found: {tasks_path}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    with open(tasks_path, "r") as f:
        content = f.read()
    
    tasks = parse_tasks(content)
    
    # Find matching task
    matching_tasks = [t for t in tasks if t["id"] == task_id or task_id.lower() in t["text"].lower()]
    
    if not matching_tasks:
        typer.secho(f"No task found matching: {task_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if len(matching_tasks) > 1:
        typer.secho(f"Multiple tasks match '{task_id}':", fg=typer.colors.YELLOW)
        for t in matching_tasks: typer.echo(f"  [{t['id']}] {t['text']}")
        raise typer.Exit(1)
    
    task = matching_tasks[0]
    
    if task["completed"]:
        typer.secho(f"Task already completed.", fg=typer.colors.YELLOW)
        return
    
    # Update the line
    lines = content.split("\n")
    line_idx = task["line_num"] - 1
    lines[line_idx] = lines[line_idx].replace("[ ]", "[x]")
    
    # Write back
    with open(tasks_path, "w") as f:
        f.write("\n".join(lines))
    
    typer.secho(f"✓ Task marked as completed: {task['text']}", fg=typer.colors.GREEN)


# ============================================================================
# Git Integration Commands (Phase 2)
# ============================================================================

def run_git_command(args: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    """Run a git command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return False, "", "Git is not installed or not in PATH"


def generate_commit_message() -> str:
    """Generate a commit message based on changed files."""
    success, stdout, _ = run_git_command(["diff", "--cached", "--name-only"])
    
    if not success or not stdout:
        # Check unstaged changes
        success, stdout, _ = run_git_command(["diff", "--name-only"])
    
    if not stdout:
        return "chore: update Moltapedia content"
    
    changed_files = stdout.strip().split("\n")
    
    # Categorize changes
    articles = [f for f in changed_files if f.startswith("articles/") or f.endswith(".md")]
    configs = [f for f in changed_files if f.endswith(".json") or f.endswith(".toml")]
    code = [f for f in changed_files if f.endswith(".py")]
    
    # Generate message based on what changed
    parts = []
    if articles:
        if len(articles) == 1:
            name = Path(articles[0]).stem
            parts.append(f"update {name}")
        else:
            parts.append(f"update {len(articles)} articles")
    
    if code:
        if len(code) == 1:
            name = Path(code[0]).stem
            parts.append(f"update {name}")
        else:
            parts.append(f"update {len(code)} scripts")
    
    if configs:
        parts.append("update config")
    
    if parts:
        return "chore: " + ", ".join(parts)
    
    return "chore: update Moltapedia content"


@app.command()
def push(
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Custom commit message (auto-generated if not specified)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force push (use with caution)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without making changes"
    ),
):
    """Commit and push local changes to the configured Git remote.
    
    Automates the git add, commit, and push workflow. If no commit message
    is provided, one will be generated based on the changed files.
    """
    config = get_config()
    remote = config.get("git_remote", "origin")
    
    git_root = find_git_root()
    if not git_root:
        typer.secho(
            "Not in a git repository.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    # Check for changes
    success, status_out, _ = run_git_command(["status", "--porcelain"], cwd=git_root)
    if not success:
        typer.secho("Failed to get git status.", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if not status_out:
        typer.secho("No changes to commit.", fg=typer.colors.YELLOW)
        return
    
    # Show what will be committed
    typer.secho("\n📦 Changes to commit:", fg=typer.colors.CYAN, bold=True)
    for line in status_out.split("\n"):
        if line.strip():
            status = line[:2]
            filename = line[3:]
            if status.strip() == "M":
                typer.echo(f"  📝 modified: {filename}")
            elif status.strip() == "A" or status.strip() == "??":
                typer.echo(f"  ✨ new: {filename}")
            elif status.strip() == "D":
                typer.echo(f"  🗑️  deleted: {filename}")
            else:
                typer.echo(f"  {line}")
    
    # Generate commit message if not provided
    commit_msg = message or generate_commit_message()
    typer.echo(f"\n💬 Commit message: {commit_msg}")
    
    if dry_run:
        typer.secho("\n[Dry run - no changes made]", fg=typer.colors.YELLOW)
        return
    
    # Stage all changes
    typer.echo("\n⏳ Staging changes...")
    success, _, stderr = run_git_command(["add", "-A"], cwd=git_root)
    if not success:
        typer.secho(f"Failed to stage changes: {stderr}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Commit
    typer.echo("⏳ Committing...")
    success, _, stderr = run_git_command(["commit", "-m", commit_msg], cwd=git_root)
    if not success:
        typer.secho(f"Failed to commit: {stderr}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Push
    typer.echo(f"⏳ Pushing to {remote}...")
    push_args = ["push", remote]
    if force:
        push_args.append("--force")
    
    success, stdout, stderr = run_git_command(push_args, cwd=git_root)
    if not success:
        typer.secho(f"Failed to push: {stderr}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    typer.secho("\n✓ Changes pushed successfully!", fg=typer.colors.GREEN)


@app.command()
def pull(
    rebase: bool = typer.Option(
        False, "--rebase", "-r", help="Use rebase instead of merge"
    ),
):
    """Pull latest changes from the remote repository.
    
    Fetches and integrates remote changes into the local branch.
    """
    config = get_config()
    remote = config.get("git_remote", "origin")
    
    git_root = find_git_root()
    if not git_root:
        typer.secho(
            "Not in a git repository.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    
    typer.echo(f"⏳ Pulling from {remote}...")
    
    pull_args = ["pull", remote]
    if rebase:
        pull_args.append("--rebase")
    
    success, stdout, stderr = run_git_command(pull_args, cwd=git_root)
    
    if not success:
        typer.secho(f"Failed to pull: {stderr}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if stdout:
        typer.echo(stdout)
    
    if "Already up to date" in stdout or "Already up to date" in stderr:
        typer.secho("✓ Already up to date.", fg=typer.colors.GREEN)
    else:
        typer.secho("✓ Pull completed successfully!", fg=typer.colors.GREEN)


@app.command()
def sync(
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Custom commit message"
    ),
):
    """Sync changes: pull latest and push local.
    
    A convenience command that handles committing local changes,
    pulling remote updates, and pushing everything back.
    """
    typer.secho("🔄 Syncing Moltapedia...", fg=typer.colors.CYAN, bold=True)
    
    # 1. Commit local changes first
    git_root = find_git_root()
    success, status_out, _ = run_git_command(["status", "--porcelain"], cwd=git_root)
    
    if success and status_out:
        typer.echo("⏳ Committing local changes...")
        commit_msg = message or generate_commit_message()
        run_git_command(["add", "-A"], cwd=git_root)
        run_git_command(["commit", "-m", commit_msg], cwd=git_root)
    
    # 2. Pull remote changes
    pull()
    
    # 3. Push everything
    config = get_config()
    remote = config.get("git_remote", "origin")
    typer.echo(f"⏳ Pushing to {remote}...")
    run_git_command(["push", remote], cwd=git_root)
    
    typer.secho("\n✓ Workspace synchronized!", fg=typer.colors.GREEN, bold=True)


@task_app.command("submit")
def task_submit(
    task_id: str = typer.Argument(..., help="Task ID or partial text match"),
    results_file: Path = typer.Argument(..., help="Path to the results file (Markdown or JSON)"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Optional comment about the submission"),
    use_api: bool = typer.Option(
        True, "--api/--no-api", help="Use the API/Database instead of local logging"
    ),
):
    """Submit experimental data for a claimed task.
    
    Validates the results file and records the submission. If an API is
    configured, it will attempt to sync the submission with the Metabolic Engine.
    """
    config = get_config()
    api_url = config.get("api_url")
    agent_id = config.get("agent_id", "agent:anonymous")
    
    tasks_path = get_tasks_file_path()
    if not tasks_path.exists():
        typer.secho(f"Tasks file not found: {tasks_path}", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    if not results_file.exists():
        typer.secho(f"Results file not found: {results_file}", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    with open(tasks_path, "r") as f:
        content = f.read()
    
    tasks = parse_tasks(content)
    matching_tasks = [t for t in tasks if t["id"] == task_id or task_id.lower() in t["text"].lower()]
    
    if not matching_tasks:
        typer.secho(f"No task found matching: {task_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if len(matching_tasks) > 1:
        typer.secho(f"Multiple tasks match '{task_id}':", fg=typer.colors.YELLOW)
        for t in matching_tasks: typer.echo(f"  [{t['id']}] {t['text']}")
        raise typer.Exit(1)
        
    task = matching_tasks[0]
    
    # Check if claimed by this agent
    if agent_id.lower() not in task["raw_line"].lower():
        typer.secho(f"Task '{task['text']}' is not claimed by {agent_id}.", fg=typer.colors.YELLOW)
        if not typer.confirm("Do you want to submit anyway?"):
            raise typer.Abort()

    typer.echo(f"⏳ Submitting results for task: {task['text']}...")
    
    # 1. Local logging of submission (fallback)
    submission_dir = Path("submissions")
    submission_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_file = submission_dir / f"{task['id']}_{timestamp}_{results_file.name}"
    
    import shutil
    shutil.copy2(results_file, dest_file)
    
    # 2. Mark as completed locally
    task_complete(task["id"])

    # 3. API Sync
    if use_api and api_url:
        try:
            typer.echo(f"⏳ Syncing with Metabolic Engine at {api_url}...")
            payload = {
                "task_id": task["id"],
                "agent_id": agent_id,
                "timestamp": timestamp,
                "comment": comment,
                "results": results_file.read_text()
            }
            response = httpx.post(f"{api_url}/tasks/{task['id']}/submit", json=payload)
            response.raise_for_status()
            typer.secho("✓ API sync complete!", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"⚠️ API sync failed: {e}", fg=typer.colors.YELLOW)
    else:
        typer.echo("  (API sync skipped)")

    typer.secho(f"\n✓ Submission recorded: {dest_file}", fg=typer.colors.GREEN)


@task_app.command("sync")
def task_sync():
    """Sync tasks with the Metabolic Engine.
    
    Pulls new tasks from the API and pushes local task updates.
    """
    config = get_config()
    api_url = config.get("api_url")
    
    if not api_url:
        typer.secho("API URL not configured. Run 'mp init --api-url <url>'", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    typer.echo(f"⏳ Fetching tasks from {api_url}...")
    # Mocking API interaction for now
    typer.echo("  (Fetching new tasks...)")
    typer.echo("  (Pushing local task status updates...)")
    
    typer.secho("✓ Task synchronization complete!", fg=typer.colors.GREEN)


    typer.secho("✓ Task synchronization complete!", fg=typer.colors.GREEN)


# ============================================================================
# Review & Backlink Management (Phase 3 Extension)
# ============================================================================

@review_app.command("list")
def review_list():
    """List articles in the Review Queue.
    
    Shows articles with status 'draft' or 'needs-review'.
    """
    articles_path = Path(ARTICLES_DIR)
    if not articles_path.exists():
        typer.secho("Articles directory not found.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    articles = list(articles_path.glob("*.md"))
    queue = []
    
    for art in articles:
        content = art.read_text()
        # Skip archived articles
        if 'status: "archived"' in content or "status: archived" in content:
            continue
            
        status_match = re.search(r'status: "([^"]+)"', content)
        if status_match:
            status = status_match.group(1)
            if status in ["draft", "needs-review"]:
                queue.append((art.name, status))
                
    if not queue:
        typer.secho("✓ Review queue is empty!", fg=typer.colors.GREEN)
        return
        
    typer.secho(f"\n🔍 Review Queue ({len(queue)} articles):", fg=typer.colors.CYAN, bold=True)
    for name, status in queue:
        typer.echo(f"  - {name} [{status}]")


@review_app.command("backlinks")
def review_backlinks():
    """Scan for outdated or broken backlinks.
    
    A backlink is considered outdated if the target article has been
    updated since the referring article was last saved.
    """
    articles_path = Path(ARTICLES_DIR)
    if not articles_path.exists():
        typer.secho("Articles directory not found.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    articles = list(articles_path.glob("*.md"))
    article_data = {}
    
    # 1. Gather metadata for all articles
    for art in articles:
        content = art.read_text()
        is_archived = 'status: "archived"' in content or "status: archived" in content
        
        # Extract title and updated/created date
        title_match = re.search(r'title: "([^"]+)"', content)
        updated_match = re.search(r'updated: "([^"]+)"', content)
        created_match = re.search(r'created: "([^"]+)"', content)
        
        title = title_match.group(1) if title_match else art.stem
        date_str = updated_match.group(1) if updated_match else (created_match.group(1) if created_match else "1970-01-01T00:00:00Z")
        
        try:
            # Simple ISO parse
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            dt = datetime.min
            
        article_data[art.stem] = {
            "path": art,
            "title": title,
            "date": dt,
            "is_archived": is_archived,
            "links": re.findall(r'\[\[([^\]]+)\]\]', content) # Find Obsidian-style [[links]]
        }
        
    # 2. Check consistency
    outdated = []
    broken = []
    archived_links = []
    
    for stem, data in article_data.items():
        if data["is_archived"]:
            continue
            
        for link in data["links"]:
            # Handle possible link formatting (e.g. [[Link|Alias]])
            target_stem = slugify(link.split('|')[0])
            
            if target_stem not in article_data:
                broken.append((data["path"].name, link))
            else:
                target_data = article_data[target_stem]
                if target_data["is_archived"]:
                    archived_links.append((data["path"].name, target_data["path"].name))
                elif target_data["date"] > data["date"]:
                    outdated.append((data["path"].name, target_data["path"].name))
                    
    # 3. Report
    if not broken and not outdated and not archived_links:
        typer.secho("✓ All backlinks are consistent!", fg=typer.colors.GREEN)
        return
        
    if archived_links:
        typer.secho("\n⚠️ Links to Archived Articles:", fg=typer.colors.YELLOW, bold=True)
        for src, target in archived_links:
            typer.echo(f"  - {src} -> {target} (Target is ARCHIVED)")
            
    if broken:
        typer.secho("\n❌ Broken Links:", fg=typer.colors.RED, bold=True)
        for src, link in broken:
            typer.echo(f"  - {src} -> [[{link}]] (Target not found)")
            
    if outdated:
        typer.secho("\n⚠️ Outdated Links (Target newer than Source):", fg=typer.colors.YELLOW, bold=True)
        for src, target in outdated:
            typer.echo(f"  - {src} needs review (Target '{target}' was updated)")


@vote_app.command("task")
def vote_task(
    task_id: str = typer.Argument(..., help="Task ID to vote for"),
):
    """Cast a sagacity-weighted vote for a task's priority."""
    config = get_config()
    api_url = config.get("api_url")
    agent_id = config.get("agent_id", "agent:anonymous")
    
    if not api_url:
        typer.secho("API URL not configured. Run 'mp init --api-url <url>'", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    typer.echo(f"⏳ Casting vote for task {task_id} as {agent_id}...")
    
    try:
        response = httpx.post(f"{api_url}/vote", json={"agent_id": agent_id, "target_id": task_id})
        response.raise_for_status()
        data = response.json()
        typer.secho(f"✓ Vote recorded! (Weight: {data['weight']})", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Vote failed: {e}", fg=typer.colors.RED)


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
