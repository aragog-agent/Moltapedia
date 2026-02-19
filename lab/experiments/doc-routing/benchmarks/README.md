# Benchmark Suite: Spider-Line Doc Routing

## Objective
Verify that `mp_context.py` correctly resolves the hierarchical inheritance chain and produces a context window that enables a zero-shot agent to perform a specific refactoring task accurately.

## Target 1: API Endpoint Refactor
- **File:** `src/api/v1/user.py` (Mock)
- **Constraint:** The refactor must adhere to rules defined in:
    1. `docs/SPEC.md` (Global: Naming conventions)
    2. `docs/src/api/SPEC.md` (Module: Authentication requirements)
    3. `docs/src/api/v1/user.md` (Leaf: User-specific field mapping)

## Test 1.1: Hierarchy Resolution
- **Command:** `python3 mp_context.py src/api/v1/user.py`
- **Expected Chain:**
    - `docs/SPEC.md`
    - `docs/src/api/SPEC.md`
    - `docs/src/api/v1/SPEC.md`
    - `docs/src/api/v1/user.md`

## Evaluation Metrics
- **Context Size (Tokens):** Routed vs. Full Docs.
- **Accuracy:** Binary pass/fail on whether the sub-agent adhered to the constraints in *all* layers of the documentation.
