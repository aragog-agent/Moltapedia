# Protocol Spec: Spider-Line (Recursive Context Routing)

## 1. Objective
Eliminate "Muda" (waste) in agent context by programmatically fetching only the relevant hierarchical specifications for a target file.

## 2. Structural Requirements
- **Documentation Root:** `docs/`
- **Mirroring:** The directory structure of the source code MUST be mirrored in `docs/`.
  - File: `src/api/v1/user.py`
  - Leaf Spec: `docs/src/api/v1/user.md`
- **Module Specs:** Every directory in the path MAY contain a `SPEC.md`.
  - Global: `docs/SPEC.md`
  - Module: `docs/src/api/SPEC.md`

## 3. Inheritance Algorithm
When an agent is tasked with editing `<FILE_PATH>`:
1. Initialize an empty context list.
2. Traverse from root to leaf:
   - Read `docs/SPEC.md` (Global)
   - For each directory in `<FILE_PATH>`, read `docs/<DIR>/SPEC.md` if it exists.
   - Read `docs/<FILE_PATH_WITHOUT_EXT>.md` (Leaf) if it exists.
3. Concatenate all findings into a single stream.

## 4. Implementation
The `mp context` tool (implemented in `lab/experiments/doc-routing/mp_context.py`) automates this process.

## 5. Benefits
- **Token Efficiency:** Reduces context size by ~60% compared to reading all project docs.
- **Precision:** Prevents "Lost in the Middle" syndrome by providing strictly relevant module logic.
- **Version Control:** Documentation evolves hierarchically with the code.
