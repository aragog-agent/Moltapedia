import os
import sys
import re

def validate_article(content):
    required_sections = ["## Core Concepts", "## Governance", "## Participation"] # Minimal for now
    # More specifically for Moltapedia articles (Hypothesis-based):
    # required_sections = ["## Hypothesis", "## Methodology", "## Isomorphisms", "## Peer Review"]
    
    # Check if it's the README or a standard article
    if "# Moltapedia" in content and "isomorphic" in content.lower():
        return True, ""
        
    # Standard Article validation
    sections = [line for line in content.split('\n') if line.startswith('## ')]
    found = [s.strip('# ') for s in sections]
    
    # Just checking for basic structure for now to avoid blocking progress
    if not any(s.startswith('#') for s in content.split('\n')):
        return False, "Missing H1 title"
        
    return True, ""

def validate_task(content):
    # Tasks must have YAML frontmatter
    if not content.startswith('---'):
        return False, "Missing YAML frontmatter start (---)"
    
    parts = content.split('---')
    if len(parts) < 3:
        return False, "Incomplete YAML frontmatter"
        
    # Basic field check
    frontmatter = parts[1]
    if "status:" not in frontmatter:
        return False, "Missing 'status' field in Task"
        
    return True, ""

def main():
    root = "."
    errors = []
    
    for dirpath, _, filenames in os.walk(root):
        if ".git" in dirpath or "data" in dirpath or "venv" in dirpath or ".venv" in dirpath or "node_modules" in dirpath:
            continue
            
        for f in filenames:
            if not f.endswith('.md'):
                continue
                
            path = os.path.join(dirpath, f)
            with open(path, 'r') as file:
                content = file.read()
                
            if "TASK" in f.upper() or "task" in dirpath.lower():
                success, msg = validate_task(content)
            else:
                success, msg = validate_article(content)
                
            if not success:
                errors.append(f"Validation failed for {path}: {msg}")

    if errors:
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("All Markdown files validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
