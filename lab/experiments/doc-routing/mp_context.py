#!/usr/bin/env python3
import os
import sys

def get_doc_inheritance_chain(file_path, docs_root="docs"):
    chain = []
    # Convert file path to potential doc path
    base, _ = os.path.splitext(file_path)
    chain.append(f"{docs_root}/{base}.md")
    
    # Climb the directory tree
    current_dir = os.path.dirname(file_path)
    while current_dir:
        chain.append(f"{docs_root}/{current_dir}/SPEC.md")
        current_dir = os.path.dirname(current_dir)
        
    # Always include global spec
    chain.append(f"{docs_root}/SPEC.md")
    
    # Filter for existing files and reverse (root-to-leaf)
    existing = [p for p in chain if os.path.exists(p)]
    return existing[::-1]

def aggregate_docs(file_path):
    chain = get_doc_inheritance_chain(file_path)
    if not chain:
        return f"No documentation found for {file_path}"
    
    output = []
    output.append(f"# Documentation context for: {file_path}\n")
    for doc in chain:
        output.append(f"## File: {doc}")
        try:
            with open(doc, 'r') as f:
                output.append(f.read())
        except Exception as e:
            output.append(f"Error reading {doc}: {str(e)}")
        output.append("\n---\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mp context <file_path>")
        sys.exit(1)
    
    print(aggregate_docs(sys.argv[1]))
