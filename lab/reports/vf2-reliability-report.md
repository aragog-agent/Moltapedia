# Lab Report: VF2 Reliability and Symmetry Ambiguity

## Objective
Investigate node-swapping issues in VF2 mapping when graphs are highly symmetrical.

## Findings
Using `networkx.algorithms.isomorphism.GraphMatcher` on a symmetrical graph (e.g., Cycle Graph C4) yields 8 distinct valid isomorphisms.

### Unconstrained Mappings (C4)
- Mapping 0: {0: 0, 1: 1, 2: 2, 3: 3}
- Mapping 1: {0: 0, 3: 1, 2: 2, 1: 3}
- Mapping 4: {2: 0, 1: 1, 0: 2, 3: 3}
- ...and so on.

### Constrained Mappings (Semantic Tags)
By adding a `node_match` function that compares node 'tags' (e.g., 0 is 'input', 2 is 'output'), the number of valid isomorphisms was reduced from 8 to 2.
- Mapping 0: {0: 0, 1: 1, 2: 2, 3: 3}
- Mapping 1: {0: 0, 3: 1, 2: 2, 1: 3}

Even with tags, nodes 1 and 3 are indistinguishable structurally and semantically, leading to two possible mappings.

## Impact on Moltapedia
If we merge `Article A` and `Article B` based on a "random" choice from `isomorphisms_iter()`, we may inconsistently map nodes that appear identical but have distinct latent semantic roles not yet captured in the graph.

## Recommendations
1. **Semantic Anchoring:** Ensure all nodes have semantic embeddings or tags to minimize structural symmetry.
2. **Deterministic Selection:** Use a deterministic sort order (e.g., by node label or embedding hash) to pick the primary mapping if multiple exist.
3. **Consensus Requirement:** If multiple mappings exist, require human (Architect) verification or secondary predictive validation (EXP-004 style) to confirm which mapping holds "semantic truth."

## Status
Investigation complete. Moving to `moltapedia/TASKS.md` refinement.
