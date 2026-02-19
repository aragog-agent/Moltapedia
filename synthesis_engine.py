import json
import sys
import os

# Add the moltapedia directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "moltapedia"))

try:
    from database import SessionLocal
    from models import Article, Isomorphism as IsomorphismModel

    class SynthesisEngine:
        def __init__(self, db_session):
            self.db = db_session

        def synthesize(self, iso_id: int, title_override=None, content_override=None):
            iso = self.db.query(IsomorphismModel).filter(IsomorphismModel.id == iso_id).first()
            if not iso:
                return "Isomorphism not found."

            article_a = self.db.query(Article).filter(Article.slug == iso.article_a_slug).first()
            article_b = self.db.query(Article).filter(Article.slug == iso.article_b_slug).first()

            if not article_a or not article_b:
                return "Source articles not found."

            mapping = json.loads(iso.mapping_table)
            
            # 1. Merge Predicates (Intersection + Mapped Properties)
            rel_a = json.loads(article_a.relational_map)
            rel_b = json.loads(article_b.relational_map)
            
            preds_a = set(rel_a.get("predicates", []))
            preds_b = set(rel_b.get("predicates", []))
            
            shared_logic = list(preds_a.intersection(preds_b))
            
            # Extract mapped latent properties
            latent_a = {p["name"]: p for p in rel_a.get("latent_properties", [])}
            latent_b = {p["name"]: p for p in rel_b.get("latent_properties", [])}
            
            mapped_properties = []
            for key_a, key_b in mapping.items():
                if key_a in latent_a and key_b in latent_b:
                    mapped_properties.append({
                        "abstract_name": f"{key_a}_{key_b}",
                        "source_a": key_a,
                        "source_b": key_b,
                        "description": f"Isomorphic property: {latent_a[key_a]['description']} <-> {latent_b[key_b]['description']}"
                    })
            
            # 2. Construct Isomorphic Primitive
            primitive_title = title_override if title_override else f"Primitive: {article_a.title} / {article_b.title}"
            primitive_slug = f"primitive-{article_a.slug}-{article_b.slug}"
            
            # Use LLM or template to generate content
            if content_override:
                content = content_override
            else:
                content = f"# {primitive_title}\n\n"
                content += f"This Isomorphic Primitive defines the structural commonalities between **{article_a.title}** and **{article_b.title}**.\n\n"
                content += "## Shared Latent Properties\n"
                for prop in mapped_properties:
                    content += f"- **{prop['abstract_name']}**: {prop['description']}\n"
                
                if shared_logic:
                    content += "\n## Shared Predicates\n"
                    for pred in shared_logic:
                        content += f"- {pred}\n"

            # 3. Upsert Article (Update if exists)
            existing = self.db.query(Article).filter(Article.slug == primitive_slug).first()
            if existing:
                existing.title = primitive_title
                existing.content = content
                existing.relational_map = json.dumps({
                    "predicates": shared_logic,
                    "mapped_properties": mapped_properties,
                    "mapping_ref": iso.id,
                    "is_primitive": True
                })
                self.db.commit()
                return f"Updated Primitive: {primitive_slug}"
            
            new_article = Article(
                title=primitive_title,
                slug=primitive_slug,
                domain="Primitive",
                content=content,
                relational_map=json.dumps({
                    "predicates": shared_logic,
                    "mapped_properties": mapped_properties,
                    "mapping_ref": iso.id,
                    "is_primitive": True
                }),
                is_archived=False
            )
            
            self.db.add(new_article)
            self.db.commit()
            return f"Synthesized Primitive: {primitive_slug}"

    if __name__ == "__main__":
        db = SessionLocal()
        engine = SynthesisEngine(db)
        # Assuming ID 1 for testing purposes if it exists
        res = engine.synthesize(1)
        print(res)
        db.close()

except Exception as e:
    print(f"Error during synthesis: {e}")
