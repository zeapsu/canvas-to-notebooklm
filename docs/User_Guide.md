# User Guide 📖

This guide will help you get `canvas-to-notebooklm` up and running.

## Prerequisites
- **Python 3.10+** installed on your machine.
- A **Canvas** account (student or teacher) with API access.
- A **Google** account for NotebookLM.

## Installation
First, grab the code and install the python requirements:

```bash
git clone ...
cd canvas-to-notebooklm
pip install -r requirements.txt
```

## Authentication

We need to authenticate with two services: **Google NotebookLM** and **Canvas**.

### Primary Method: `notebooklm login`
The easiest way to authenticate with Google is using the CLI provided by the `notebooklm-py` library.

1.  Run the login command:
    ```bash
    notebooklm login
    ```
2.  A browser window (or a link) should appear asking you to sign in to your Google Account.
3.  Once signed in, the tool saves your session cookies locally.

### Fallback Method: Manual Cookies
If the automated login fails (sometimes Google gets picky about automated browsers), you can manually export your cookies.

1.  install a "Get cookies.txt LOCALLY" extension for your browser (Chrome/Firefox).
2.  Go to [NotebookLM](https://notebooklm.google.com/) and make sure you are logged in.
3.  Export your cookies to a file named `cookies.txt`.
4.  Place this file in the project root or configure `notebooklm-py` to use it (check library docs for specific path if needed, usually `~/.notebooklm/cookies.txt` or similar).

## Configuration

### Canvas API Token
You need a token so the script can talk to Canvas on your behalf.

1.  Log in to your Canvas dashboard.
2.  Click **Account** (your profile icon) -> **Settings**.
3.  Scroll down to **Approved Integrations**.
4.  Click **+ New Access Token**.
5.  Give it a purpose (e.g., "NotebookLM Sync") and an expiration date (optional).
6.  **Copy the token immediately!** You won't be able to see it again.

### Environment Variables
Set these variables in your terminal before running the script:

**Mac/Linux:**
```bash
export CANVAS_URL="https://canvas.instructure.com"
export CANVAS_KEY="<your_token_here>"
```

**Windows (PowerShell):**
```powershell
$env:CANVAS_URL="https://canvas.instructure.com"
$env:CANVAS_KEY="<your_token_here>"
```

## Usage

### Interactive Menu
By default, running the script launches the interactive main menu:

```bash
python main.py
```

You will see the following options:
1.  **Sync All Active Courses**: Fetches every active course from Canvas. Great for first-time setup.
2.  **Update Managed Courses Only**: Only checks courses you have previously synced. Faster for daily updates.
3.  **Delete Courses**: Remove courses from the local database (useful if you dropped a class).
4.  **Exit**: Quits the tool.

### Command Line Arguments (Automation)
You can skip the menu for automated workflows (e.g., cron jobs):

| Flag | Description |
|---|---|
| `-y`, `--yes` | Skip all confirmation prompts (auto-confirm). |
| `--update-existing` | Only check courses already in the local DB. |
| `--interactive` | Force the menu to appear (default behavior). |

**Example: Daily cron job**
```bash
python main.py -y --update-existing
```

### Logging
The tool creates a `canvas_sync.log` file in the project directory. Check this file for detailed error messages or to see what files were processed.

## Troubleshooting

### "Google Login Failed"
- Try the **Fallback Method** above.
- Ensure you don't have 2FA blocking the script (though the manual login usually handles this).

### "Canvas 401 Unauthorized"
- Double-check your `CANVAS_KEY`. Did you copy the whole string?
- Make sure your `CANVAS_URL` is correct (it should be the base URL, e.g., `https://canvas.myuni.edu`, not a long path).

### "Files not showing up"
- The script currently filters for common document types. Check `main.py` if you need to allow other extensions.
