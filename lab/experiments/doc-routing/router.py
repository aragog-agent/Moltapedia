import os
import sys

def get_doc_inheritance_chain(file_path, docs_root="docs"):
    """
    Calculates the documentation files an agent should read based on the 
    recursive inheritance hypothesis.
    """
    chain = []
    # Convert file path to potential doc path
    # e.g., mp/main.py -> docs/mp/main.md
    base, ext = os.path.splitext(file_path)
    chain.append(f"{docs_root}/{base}.md")
    
    # Climb the directory tree
    current_dir = os.path.dirname(file_path)
    while current_dir:
        chain.append(f"{docs_root}/{current_dir}/SPEC.md")
        current_dir = os.path.dirname(current_dir)
        
    # Always include global spec
    chain.append(f"{docs_root}/SPEC.md")
    
    return [p for p in chain if os.path.exists(p)]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 router.py <file_path>")
        sys.exit(1)
    
    print("Inheritance Chain for:", sys.argv[1])
    for doc in get_doc_inheritance_chain(sys.argv[1]):
        print(f"- {doc}")
