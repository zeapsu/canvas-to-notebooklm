import sys
import asyncio
import os
import argparse
import logging
from dotenv import load_dotenv
from canvas_client import CanvasClient
from state_manager import StateManager
from notebook_client import NotebookLMClientWrapper

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("canvas_sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables from .env file
load_dotenv()

# Configuration
CANVAS_URL = os.environ.get("CANVAS_URL", "https://canvas.instructure.com")
CANVAS_KEY = os.environ.get("CANVAS_KEY", "")

def setup_args():
    parser = argparse.ArgumentParser(description="Canvas to NotebookLM Sync Tool")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts (assume yes to all)")
    parser.add_argument("--update-existing", action="store_true", help="Only sync courses that already exist in the local database")
    parser.add_argument("--interactive", action="store_true", help="Launch the interactive main menu (default if no other args provided)")
    return parser.parse_args()

async def sync_courses(canvas_client, state_manager, notebook_client, args):
    """
    Main Logic to sync courses.
    """
    logging.info("Starting Sync...")
    courses_to_process = []

    # 1. Determine which courses to look at
    if args.update_existing:
        logging.info("Mode: Update Existing Managed Courses Only")
        managed_courses = state_manager.get_all_managed_courses() # [(id, name, nb_id), ...]
        managed_ids = [c[0] for c in managed_courses]
        
        # We still need to fetch the course objects from Canvas to get the file list
        # This is slightly inefficient if we have to fetch *all* to find them, 
        # but canvas_client.get_active_courses() is usually the best way to get 'current' stuff.
        # Alternatively, we could fetch by ID if API supports it, but loop is safer for now.
        all_active = canvas_client.get_active_courses()
        courses_to_process = [c for c in all_active if str(c.id) in managed_ids]
    else:
        logging.info("Mode: Sync All Active Courses")
        courses_to_process = canvas_client.get_active_courses()

    # 2. Iterate
    for course in courses_to_process:
        try:
            course_id = str(course.id)
            course_name = getattr(course, 'name', f"Course {course_id}")
            
            # Interactive Confirmation for Course
            if not args.yes:
                print(f"\nFound Course: {course_name} (ID: {course_id})")
                choice = input("Sync this course? [Y/n]: ").strip().lower()
                if choice == 'n':
                    logging.info(f"Skipping course: {course_name}")
                    continue

            logging.info(f"Processing Course: {course_name}")
            
            # 3. Check/Create Notebook
            nb_id = state_manager.get_course_notebook_id(course_id)
            if not nb_id:
                # Confirm Creation
                if not args.yes:
                    choice = input(f"Notebook for '{course_name}' does not exist. Create it? [Y/n]: ").strip().lower()
                    if choice == 'n':
                        logging.info(f"Skipping notebook creation for: {course_name}")
                        continue
                
                try:
                    nb_id = await notebook_client.create_notebook(course_name)
                    state_manager.set_course_notebook_id(course_id, nb_id, course_name)
                    logging.info(f"Created Notebook: {course_name}")
                except Exception as e:
                    logging.error(f"Failed to create notebook for {course_name}: {e}")
                    continue
            else:
                 logging.info(f"Using existing Notebook ID: {nb_id}")

            # 4. Process Files
            files = canvas_client.get_course_files(course.id)
            for file in files:
                file_id = str(file.id)
                file_name = getattr(file, 'filename', f"file_{file_id}")
                
                # Filter logic can go here (extensions etc.)
                if not file_name.endswith(('.pdf', '.docx', '.txt', '.md', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.html')):
                    logging.info(f"Skipping file: {file_name}")
                    continue

                if not state_manager.is_file_processed(file_id):
                    logging.info(f"New file found: {file_name}")
                    
                    # Ensure download dir exists
                    download_dir = os.path.join(os.getcwd(), "temp_downloads", f"{course_id}")
                    local_path = os.path.join(download_dir, file_name)
                    
                    try:
                        download_url = getattr(file, 'url', None)
                        if download_url:
                            canvas_client.download_file(download_url, local_path)
                            await notebook_client.upload_source(nb_id, local_path)
                            state_manager.mark_file_processed(file_id, course_id, file_name)
                            logging.info(f"Successfully processed {file_name}")
                    except Exception as e:
                         logging.error(f"Error processing file {file_name}: {e}")
                    finally:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                else:
                    logging.debug(f"File already processed: {file_name}")

        except Exception as e:
            logging.error(f"Error processing course object: {e}")

    logging.info("Sync Complete.")

async def delete_courses_flow(state_manager):
    """
    Interactive flow to delete courses.
    """
    managed = state_manager.get_all_managed_courses()
    if not managed:
        print("No managed courses found in database.")
        return

    print("\n--- Managed Courses ---")
    # managed is list of (id, name, nb_id)
    for idx, (cid, name, nbid) in enumerate(managed):
        print(f"{idx + 1}. {name} (ID: {cid})")
    
    print("\nEnter the numbers of the courses to delete (separated by space), or 'q' to cancel.")
    selection = input("Selection: ").strip()
    
    if selection.lower() == 'q':
        return

    try:
        indices = [int(x) - 1 for x in selection.split()]
        for i in indices:
            if 0 <= i < len(managed):
                course_to_delete = managed[i]
                cid, name, _ = course_to_delete
                
                confirm = input(f"Are you sure you want to delete '{name}' from local DB? (This does not delete the NotebookLM notebook) [y/N]: ").lower()
                if confirm == 'y':
                    if state_manager.delete_course(cid):
                        print(f"Deleted '{name}'.")
                    else:
                        print(f"Failed to delete '{name}'.")
    except ValueError:
        print("Invalid input.")

async def main():
    if not CANVAS_KEY:
         logging.error("CANVAS_KEY not set. Please set CANVAS_URL and CANVAS_KEY env vars.")
         return

    args = setup_args()

    # Initialize modules
    state_manager = StateManager()
    canvas_client = CanvasClient(CANVAS_URL, CANVAS_KEY)
    notebook_client = NotebookLMClientWrapper()

    # Check/Force Interactive Mode if no args
    # If -y or --update-existing is passed, we assume we skip the menu and go straight to sync, 
    # unless --interactive is ALSO passed (which would be weird but manageable).
    # Default behavior: If no args, show menu.
    show_menu = args.interactive or (not args.yes and not args.update_existing)

    if show_menu:
        while True:
            print("\n=== Canvas to NotebookLM Main Menu ===")
            print("1. Sync All Active Courses")
            print("2. Update Managed Courses Only")
            print("3. Delete Courses from DB")
            print("4. Exit")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                # Sync All
                # We reuse the args object but force flags
                args.update_existing = False
                # User can still be prompted inside sync unless they passed -y to the script originally
                await sync_courses(canvas_client, state_manager, notebook_client, args)
            elif choice == '2':
                # Sync managed only
                args.update_existing = True
                await sync_courses(canvas_client, state_manager, notebook_client, args)
            elif choice == '3':
                await delete_courses_flow(state_manager)
            elif choice == '4':
                print("Exiting.")
                break
            else:
                print("Invalid option.")
    else:
        # Headless / Direct Mode
        await sync_courses(canvas_client, state_manager, notebook_client, args)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
