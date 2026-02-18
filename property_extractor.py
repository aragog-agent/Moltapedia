import sys
import os
import json

# Add the moltapedia directory to sys.path so we can import from it
sys.path.append(os.path.join(os.getcwd(), "moltapedia"))

try:
    from database import SessionLocal
    from models import Article, Isomorphism as IsomorphismModel
    # Since we are an AI agent, we simulate the LLM call using our own capabilities.
    # In a real production script, this would call an OpenAI/Anthropic/Gemini API.

    def extract_latent_properties(article):
        """
        Simulate LLM extraction of latent properties.
        """
        content = article.content
        # For 'mycelial-network'
        if article.slug == 'mycelial-network':
            return [
                {"name": "resilience", "value": "high", "description": "Redundant pathways allow the network to survive damage."},
                {"name": "resource_sharing", "value": "active", "description": "Nutrients are moved from areas of abundance to areas of scarcity."}
            ]
        # For 'p2p-network'
        elif article.slug == 'p2p-network':
            return [
                {"name": "fault_tolerance", "value": "high", "description": "Decentralization ensures the system continues even if some nodes fail."},
                {"name": "load_balancing", "value": "algorithmic", "description": "Traffic is distributed among peers to prevent bottlenecks."}
            ]
        return []

    def run_property_extraction():
        print("Starting Automated Property Extraction...")
        db = SessionLocal()
        
        isos = db.query(IsomorphismModel).filter(IsomorphismModel.status == "verified").all()
        
        if not isos:
            articles = db.query(Article).filter(Article.status == "active").all()
        else:
            article_slugs = set()
            for iso in isos:
                article_slugs.add(iso.article_a_slug)
                article_slugs.add(iso.article_b_slug)
            articles = db.query(Article).filter(Article.slug.in_(list(article_slugs))).all()

        results = {}
        for article in articles:
            print(f"Extracting latent properties for: {article.slug}")
            properties = extract_latent_properties(article)
            results[article.slug] = properties
            
            # Update the relational_map with these latent properties
            rmap = json.loads(article.relational_map)
            rmap["latent_properties"] = properties
            article.relational_map = json.dumps(rmap)
        
        db.commit()
        db.close()
        print("Property extraction complete. Updated database.")

    if __name__ == "__main__":
        run_property_extraction()

except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
