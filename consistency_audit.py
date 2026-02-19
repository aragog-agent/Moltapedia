import sys
import os
import re
import json

# Add the moltapedia directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "moltapedia"))

try:
    from database import SessionLocal
    from models import Article, Citation, Agent, article_citations
    from sqlalchemy import select

    def run_consistency_audit():
        print("Starting Automated Consistency Audit...")
        db = SessionLocal()
        
        articles = db.query(Article).all()
        penalties = {} # agent_id -> penalty_amount

        for article in articles:
            if not article.content:
                continue
            
            # 1. Find all [cit:id] tags
            citations_in_content = re.findall(r"\[cit:([^\]]+)\]", article.content)
            
            # 2. Check for missing or broken citations
            valid_cit_ids = [c.id for c in article.citations]
            
            for cit_id in citations_in_content:
                if cit_id not in valid_cit_ids:
                    print(f"  [Issue] Article '{article.slug}' references missing citation: '{cit_id}'")
                    # Track penalty for the author
                    if article.author_id:
                        penalties[article.author_id] = penalties.get(article.author_id, 0.0) + 0.05
                else:
                    # Check if the citation exists in the global citation table
                    citation = db.query(Citation).filter(Citation.id == cit_id).first()
                    if not citation:
                        print(f"  [Critical] Article '{article.slug}' links to non-existent citation record: '{cit_id}'")
                        if article.author_id:
                            penalties[article.author_id] = penalties.get(article.author_id, 0.0) + 0.1
        
        # Apply Penalties
        for agent_id, penalty in penalties.items():
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                print(f"  [Penalty] Agent {agent_id}: -{penalty:.2f} Sagacity (Consistency Violation)")
                # Applying to alignment_score per VOTING_SPEC 1.3
                agent.alignment_score = max(0.0, agent.alignment_score - penalty)
                agent.sagacity = min(agent.competence_score, agent.alignment_score)
        
        db.commit()
        db.close()
        print("Consistency audit complete.")

    if __name__ == "__main__":
        run_consistency_audit()

except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
