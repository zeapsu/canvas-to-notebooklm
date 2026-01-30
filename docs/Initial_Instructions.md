This architecture outlines a Python-based automation solution. It is designed to be modular so you can swap out the "NotebookLM" component if the unofficial methods change (a common risk with non-public APIs).

### **High-Level System Architecture**

The system consists of three main logical modules:
1.  **Canvas Connector:** Extracts course data and files using the official Canvas API.
2.  **State Manager:** Maintains a local memory (database) to track which classes and files have already been processed to avoid duplicates.
3.  **NotebookLM Integrator:** Handles the upload logic, using an unofficial API wrapper (or browser automation) to interface with Google NotebookLM.

---

### **1. Module: Canvas Connector (`canvas_client.py`)**
**Goal:** Authenticate with Canvas and download course materials.
*   **Authentication:** Uses an API Token generated from the Canvas User Settings.
*   **Library Recommendation:** `canvasapi` (Official-ish Python library) or standard `requests` for flexibility.
*   **Key Functions:**
    *   `get_active_courses()`: Returns a list of current semester courses.
    *   `get_course_files(course_id)`: Recursively fetches all files (PDFs, PPTXs, DOCXs) from a specific course.
    *   `download_file(file_url, destination_path)`: Downloads the actual file content to a temporary directory.

### **2. Module: State Manager (`state_manager.py`)**
**Goal:** act as the "brain" to remember what has been done.
*   **Storage:** `sqlite3` (built-in to Python) or a simple `state.json` file.
*   **Schema (Concept):**
    *   `courses_table`: `course_id`, `course_name`, `notebook_lm_id` (the ID of the created notebook), `last_synced_at`.
    *   `files_table`: `file_id`, `course_id`, `file_name`, `upload_status`.
*   **Logic:**
    *   Before downloading, check if `file_id` exists in the DB. If yes, skip.
    *   When uploading to NotebookLM, if the course exists in `courses_table`, retrieve the `notebook_lm_id`. If not, flag it to create a new one.

### **3. Module: NotebookLM Integrator (`notebook_client.py`)**
**Goal:** Upload files to NotebookLM.
*   **Constraint:** There is **no official public API** for the consumer version of NotebookLM. You must use a workaround.
*   **Recommended Approach (Unofficial API):** Use a Python wrapper like `notebooklm-py` (available on GitHub/PyPI). This library reverse-engineers the internal Google RPC calls, allowing for faster, headless uploads without opening a visible browser.
*   **Fallback Approach (Browser Automation):** Use `Playwright` or `Selenium`. This physically opens a Chrome window, clicks "Create Notebook," and "Upload Source." It is slower and more brittle but easier to debug visually.
*   **Key Functions:**
    *   `login()`: Handles Google authentication (likely requires an initial manual login to save cookies/tokens).
    *   `create_notebook(title)`: Creates a new notebook and returns its ID.
    *   `upload_source(notebook_id, file_path)`: Uploads a local file to the specific notebook.

---

### **4. Main Controller (`main.py`)**
**Goal:** The conductor that ties everything together.
**Workflow Logic:**
1.  **Initialize:** Load local state and connect to Canvas.
2.  **Fetch Courses:** Get list of active courses from Canvas.
3.  **Loop through Courses:**
    *   **Check State:** Query State Manager: "Do we have a NotebookLM ID for this course?"
    *   **Action (Match Found):** If yes, use existing ID.
    *   **Action (No Match):** Call `notebook_client.create_notebook(course_name)`, save the new ID to State Manager.
4.  **Process Files:**
    *   Fetch file list for the course.
    *   Filter files (e.g., ignore images, keep PDFs/DOCs).
    *   **Check State:** "Has file X been uploaded?"
    *   **Upload:** If new, download from Canvas -> Upload to NotebookLM -> Update State Manager.
5.  **Cleanup:** Delete temporary downloaded files to save space.