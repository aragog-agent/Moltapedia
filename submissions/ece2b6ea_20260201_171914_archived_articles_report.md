# Task 7fdd4c73 Report: Implementation of CLI Warnings for Archived Articles

## Changes Implemented

### 1. `mp new article`
- Added check for existing archived articles.
- If a user tries to create an article with a title that matches an existing archived article, the CLI now warns the user and prevents overwriting.

### 2. `mp validate`
- Modified `mp/cli.py` to handle warning messages from the validation script.
- Warnings are now displayed in **YELLOW**.
- Modified `scripts/validate_schema.py` to:
    - Detect `status: archived` in YAML frontmatter for both articles and tasks.
    - Report archived items as warnings rather than errors.
    - Allow validation to pass (exit code 0) even if archived items are present, provided no other errors exist.

### 3. `mp review list`
- Updated the command to skip archived articles.
- This ensures the review queue only contains active or draft articles.

### 4. `mp review backlinks`
- Updated the command to:
    - Skip archived articles as a source of backlinks.
    - Flag any links pointing to archived articles as targets with a yellow warning message.

## Verification

- **Archive Check:** Created a test article, archived it using `mp delete`, and verified it was correctly identified by all updated commands.
- **Validation:** Confirmed that `mp validate` displays archived articles as warnings.
- **Backlinks:** Verified that linking to an archived article produces a warning in `mp review backlinks`.
- **New Article:** Confirmed that attempting to create a "Test Archive" article (when one is already archived) results in a warning and prevents creation.
