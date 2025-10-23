# UV Quick Reference Guide

## Common Commands

| Task | Command |
|------|---------|
| Setup new project | `uv sync` |
| Add package | `uv add pandas` |
| Remove package | `uv remove pandas` |
| Run script | `uv run python script.py` |
| Run tests | `uv run pytest` |
| Change Python version | `uv python install 3.12` then `uv venv --python 3.12` |
| Update dependencies | `uv lock --upgrade` |
| List packages | `uv pip list` |
| View dependency tree | `uv tree` |

---

## Workflow 1: Starting from Scratch

```bash
# 1. Create project directory
mkdir my-project && cd my-project

# 2. Initialize new project (creates pyproject.toml)
uv init

# 3. Add dependencies
uv add pandas numpy scikit-learn matplotlib jupyter

# 4. Add dev dependencies
uv add --dev pytest ruff

# 5. Setup complete - start coding!
uv run python main.py

# 6. Commit to git
git add pyproject.toml uv.lock .python-version
git commit -m "Initial project setup"
```

---

## Workflow 2: Convert from requirements.txt

```bash
# 1. Clone repo with requirements.txt
git clone <repo-url>
cd project-name

# 2. Initialize pyproject.toml
uv init

# 3. Install from requirements.txt (one-time)
uv pip install -r requirements.txt

# 4. Add packages to pyproject.toml (converts to modern format)
# Read requirements.txt and add each package:
cat requirements.txt
# Then add them:
uv add pandas numpy scikit-learn matplotlib jupyter pytest

# 5. Verify everything works
uv sync
uv run pytest

# 6. Delete old requirements.txt (optional)
rm requirements.txt

# 7. Commit the modernized setup
git add pyproject.toml uv.lock .python-version
git rm requirements.txt
git commit -m "Migrate from requirements.txt to pyproject.toml"
```

---

## After Cloning a uv Project

```bash
# 1. Clone repo
git clone <repo-url>
cd project-name

# 2. One command to setup everything
uv sync

# 3. Ready to work!
uv run python main.py
```

---

## What to Commit to Git

```
✅ pyproject.toml      # Project dependencies and metadata
✅ uv.lock             # Exact versions for reproducibility
✅ .python-version     # Python version for the project
✅ .gitignore          # Ignore rules
❌ .venv/              # Virtual environment (never commit)
❌ __pycache__/        # Python cache files
```

---

## Key Concepts

- **`uv sync`** - Creates venv and installs from `uv.lock` (reproducible)
- **`uv add`** - Adds package to `pyproject.toml` and updates `uv.lock`
- **`uv remove`** - Removes package from `pyproject.toml` and updates `uv.lock`
- **`uv run`** - Runs commands in the virtual environment (no activation needed)
- **`uv.lock`** - Lock file with exact versions (like `package-lock.json` for npm)
