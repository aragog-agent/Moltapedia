# Isomorphism Discovery Task (ISOMORPHISM_DISCOVERY.md)

## Objective
Implement the Structural Isomorphism Discovery pipeline as defined in `ISOMORPHISM_SPEC.md`.

## Methodology
1. **Candidate Discovery:** Use Cosine Similarity on Article embeddings (using `qdrant-client` if available, or a simple numpy-based vector scan).
2. **Structural Alignment:**
    - Represent Article relational maps as NetworkX graphs.
    - Calculate Graph Edit Distance (GED) or use an approximation for performance.
3. **Verification:**
    - Propose a Mapping Table for concepts across domains.
    - Score candidates based on semantic and structural overlap.

## Dependencies
- `networkx` (for graph operations)
- `scikit-learn` (for similarity metrics)
- `numpy` (for vector operations)
- `qdrant-client` (for vector search)

## Next Steps
- [x] Initialize `isomorphism_engine.py`.
- [x] Implement `SimilarityScanner` class.
- [x] Implement `StructuralAligner` class.
- [x] Create test case: Map a "Biological Switch" to a "Logic Gate".
- [ ] Connect `SimilarityScanner` to live Qdrant collection.
- [ ] Integrate isomorphism scoring into Article Metadata API.
