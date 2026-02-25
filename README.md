# Canvas to NotebookLM 🎓 ➡️ 🤖

Stop manually downloading every single PDF from Canvas. This tool automatically syncs your Canvas course files directly into Google NotebookLM, so you can turn your study materials into an AI podcast or chat with them instantly.

## Why?

Let's be real: downloading 50+ PDFs, organizing them into folders, and then manually uploading them to NotebookLM is tedious. This script does the heavy lifting for you. It connects to your Canvas account, grabs your course readings, and shoves them into NotebookLM notebooks (one per course). It even remembers what it already uploaded, so you can run it again later to catch new files without duplicates.

## Features

- **Auto-Discovery**: Finds all your active Canvas courses automatically.
- **Interactive Control**: Choose exactly which courses to sync or skip via a CLI menu.
- **Smart Sync**: Tracks files in a local SQLite database to prevent duplicates.
- **Update Only**: Option to only check courses you've already set up (faster).
- **Course Management**: Delete courses from the local database directly from the menu.
- **Hands-Free**: Uses `notebooklm-py` to handle the Google side of things.
- **Organized**: Creates a separate NotebookLM notebook for each course.

## Quick Start

1. **Clone the repo:**

   ```bash
   git clone https://github.com/zeapsu/canvas-to-notebooklm.git
   cd canvas-to-notebooklm
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Login to NotebookLM:**
   We use the nifty `notebooklm-py` library. Run this once to authenticate:

   ```bash
   uv run notebooklm login
   ```

   _Follow the instructions in the terminal to complete the login._

4. **Set your Canvas secrets:**

   ```bash
   # Copy the example env file
   cp .env.example .env
   # Edit .env with your keys
   ```

   _(Or export them manually as environment variables)_

5. **Run it:**

   ```bash
   uv run canvas-to-notebooklm
   ```

   This will launch the **Interactive Menu**.

   **Power User Flags:**

   - `uv run canvas-to-notebooklm -y`: Automated mode (yes to all).
   - `uv run canvas-to-notebooklm --sync-managed-courses -y`: Sync all managed courses non-interactively.
   - `uv run canvas-to-notebooklm --list-managed-courses` (alias: `--list-managed`): List managed courses from local DB.
   - `uv run canvas-to-notebooklm --delete "<course_id_or_name>"`: Delete one managed course from local DB.
   - `uv run canvas-to-notebooklm --delete-all -y`: Delete all managed courses from local DB.

## Dependency Management

This project uses `uv` for dependency and environment management.

- Dependency definitions live in `pyproject.toml`.
- Exact resolved versions are locked in `uv.lock`.
- Use `uv sync` after dependency changes to update your local environment.
- A CLI entrypoint is exposed as `canvas-to-notebooklm`.

### New to uv?

- Install `uv`: <https://docs.astral.sh/uv/getting-started/installation/>
- Basic usage guide: <https://docs.astral.sh/uv/getting-started/features/>

## Configuration

The tool relies on environment variables for Canvas access:

- `CANVAS_URL`: Your institution's Canvas URL (e.g., `https://canvas.uw.edu`).
- `CANVAS_KEY`: Your personal access token. [Here's how to generate one](https://community.canvaslms.com/t5/Student-Guide/How-do-I-manage-API-access-tokens-as-a-student/ta-p/273).

## Development Workflow

Install tooling and dev dependencies:

```bash
uv sync --group dev
```

Run checks locally:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy main.py canvas_client.py notebook_client.py state_manager.py
uv run pytest
```

Set up pre-commit hooks:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Docker

Build and run with Docker:

```bash
docker compose build
docker compose run --rm app
```

The default compose command is managed sync mode:

```bash
canvas-to-notebooklm --sync-managed-courses -y
```

For one-off commands:

```bash
docker compose run --rm app canvas-to-notebooklm --list-managed-courses
```

Note: NotebookLM auth still needs a valid session/cookies setup before fully headless runs.

## CI

GitHub Actions runs on push/PR and enforces:

- `ruff check`
- `ruff format --check`
- `mypy` (core modules)
- `pytest`

## Documentation

- **[User Guide](docs/User_Guide.md)**: Detailed setup, troubleshooting, and auth help.
- **[Technical Design](docs/Technical_Design_Doc.md)**: How the sausage is made (architecture, database schema).

## Contributing

Found a bug? Want to add support for quizzes? PRs are welcome! This is a chill project, just keep the code clean.

## License

MIT. Go wild.
