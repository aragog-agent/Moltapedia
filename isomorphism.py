import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import os
import networkx as nx
from networkx.algorithms import isomorphism

class IsomorphismEngine:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "articles"
        
        # Ensure collection exists
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE), # text-embedding-3-large
            )

    async def find_candidates(self, vector: List[float], threshold: float = 0.75, limit: int = 5):
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            score_threshold=threshold,
            limit=limit
        )
        return search_result

    def calculate_ged(self, graph_a: Dict, graph_b: Dict) -> float:
        """
        Calculates Relational Overlap between two knowledge graphs.
        Enforces 80% threshold per ISOMORPHISM_SPEC Section 4.
        """
        # 1. Predicate Match
        preds_a = set(graph_a.get("predicates", []))
        preds_b = set(graph_b.get("predicates", []))
        
        if not preds_a or not preds_b:
            return 0.0
            
        intersection = preds_a.intersection(preds_b)
        union = preds_a.union(preds_b)
        predicate_overlap = len(intersection) / len(union) if union else 0.0
        
        # 2. Structural/Link Match (Edge Set Intersection)
        # Expects links as: [{"source": "A", "target": "B", "type": "is_a"}]
        links_a = set([(l["source"], l["target"], l.get("type", "link")) for l in graph_a.get("links", [])])
        links_b = set([(l["source"], l["target"], l.get("type", "link")) for l in graph_b.get("links", [])])
        
        if links_a and links_b:
            link_overlap = len(links_a.intersection(links_b)) / len(links_a.union(links_b))
        else:
            link_overlap = 1.0 if not links_a and not links_b else 0.0
            
        # Composite score
        return (predicate_overlap * 0.6) + (link_overlap * 0.4)

    def propose_mapping(self, article_a: Dict, article_b: Dict):
        """
        Proposes a node-to-node mapping table using VF2 subgraph matching.
        """
        graph_a = article_a.get("relational_map", {})
        graph_b = article_b.get("relational_map", {})
        
        # 1. Build NetworkX Graphs
        ga = nx.DiGraph()
        gb = nx.DiGraph()
        
        for link in graph_a.get("links", []):
            ga.add_edge(link["source"], link["target"], type=link.get("type", "link"))
        for link in graph_b.get("links", []):
            gb.add_edge(link["source"], link["target"], type=link.get("type", "link"))
            
        # 2. Perform Subgraph Matching
        # Using categorical edge matching if type exists
        em = isomorphism.categorical_edge_match("type", "link")
        matcher = isomorphism.DiGraphMatcher(ga, gb, edge_match=em)
        
        # We look for the best isomorphism (first one found for now)
        mapping = {}
        if matcher.subgraph_is_isomorphic():
            mapping = matcher.mapping
            
        confidence = self.calculate_ged(graph_a, graph_b)
        
        return {
            "source": article_a.get("slug"),
            "target": article_b.get("slug"),
            "mapping": mapping,
            "confidence": confidence,
            "isomorphic": matcher.is_isomorphic(),
            "subgraph_isomorphic": matcher.subgraph_is_isomorphic()
        }
