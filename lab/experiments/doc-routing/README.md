# Experiment: Just-in-Time Doc Routing (Recursive Inheritance)

## Hypothesis
If documentation follows a directory-mirroring pattern, agents can programmatically fetch only the "Inheritance Chain" of specs relevant to a specific file, reducing context pollution and token burn.

## The "Spider-Line" Protocol (Draft)
1. **Directory Mirroring:** `src/api/main.py` -> `docs/src/api/main.md` or `docs/src/api/SPEC.md`.
2. **Recursive Fetch:** To edit `src/api/routes/v1/auth.py`:
   - Load `docs/src/api/routes/v1/auth.md` (Specific)
   - Load `docs/src/api/routes/v1/SPEC.md` (Directory context)
   - Load `docs/src/api/SPEC.md` (Module context)
   - Load `docs/SPEC.md` (Global context)
3. **The `mp context` Tool:** A proposed CLI command that returns the concatenated markdown of the entire inheritance line for a given path.

## Prototypes
- `router.py`: A script to calculate the doc-chain for any given file path.
