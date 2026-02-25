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
    parser.add_argument(
        "--sync-managed-courses",
        "--update-existing",
        dest="sync_managed_courses",
        action="store_true",
        help="Only sync courses that already exist in the local database",
    )
    parser.add_argument("--list-managed-courses", "--list-managed", action="store_true", help="List all managed courses in the local database")
    parser.add_argument(
        "--delete",
        dest="delete_target",
        metavar="COURSE_ID_OR_NAME",
        help="Delete a managed course from local DB by course ID or course name",
    )
    parser.add_argument("--delete-all", action="store_true", help="Delete all managed courses from local DB")
    parser.add_argument("--interactive", action="store_true", help="Launch the interactive main menu (default if no other args provided)")
    return parser.parse_args()

async def sync_courses(canvas_client, state_manager, notebook_client, args):
    """
    Main Logic to sync courses.
    """
    logging.info("Starting Sync...")
    courses_to_process = []

    # 1. Determine which courses to look at
    if args.sync_managed_courses:
        logging.info("Mode: Update Existing Managed Courses Only")
        managed_courses = state_manager.get_all_managed_courses() # [(id, name, nb_id), ...]
        if not managed_courses:
            logging.info("No managed courses found in local DB. Nothing to sync.")
            return

        if args.yes:
            logging.info("Auto-confirmed sync for all managed courses (--yes).")
        else:
            confirm = input(f"Sync all {len(managed_courses)} managed courses? [Y/n]: ").strip().lower()
            if confirm == "n":
                logging.info("Managed course sync cancelled.")
                return

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
                if file_name.endswith(('.mp3', '.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.ogg', '.wav', '.aac', '.m4a', '.wma', '.flac', '.opus', '.amr', '.aiff', '.au', '.mid', '.midi', '.rmi', '.cda', '.m4b', '.m4p', '.m4r', '.m4v', '.3gp', '.3g2', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.ogg', '.wav', '.aac', '.m4a', '.wma', '.flac', '.opus', '.amr', '.aiff', '.au', '.mid', '.midi', '.rmi', '.cda', '.m4b', '.m4p', '.m4r', '.m4v', '.3gp', '.3g2')):
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

def list_managed_courses(state_manager):
    managed = state_manager.get_all_managed_courses()
    if not managed:
        print("No managed courses found in database.")
        return []

    print("\n--- Managed Courses ---")
    for idx, (cid, name, nbid) in enumerate(managed):
        notebook_text = nbid if nbid else "None"
        print(f"{idx + 1}. {name} (ID: {cid}, Notebook ID: {notebook_text})")
    return managed


def _match_courses(managed, target):
    target_lower = target.lower()

    # 1) Exact ID match
    id_matches = [c for c in managed if str(c[0]) == target]
    if id_matches:
        return id_matches

    # 2) Exact (case-insensitive) name match
    exact_name_matches = [c for c in managed if (c[1] or "").strip().lower() == target_lower]
    if exact_name_matches:
        return exact_name_matches

    # 3) Partial (case-insensitive) name match
    partial_matches = [c for c in managed if target_lower in (c[1] or "").lower()]
    return partial_matches


def delete_managed_courses(state_manager, target, assume_yes=False):
    managed = state_manager.get_all_managed_courses()
    if not managed:
        print("No managed courses found in database.")
        return

    matches = _match_courses(managed, target)
    if not matches:
        print(f"No managed course found for '{target}'.")
        return

    if len(matches) > 1:
        print(f"Multiple matches for '{target}'. Use a course ID for precision:")
        for cid, name, _ in matches:
            print(f"- {name} (ID: {cid})")
        return

    cid, name, _ = matches[0]
    if not assume_yes:
        confirm = input(
            f"Delete '{name}' (ID: {cid}) from local DB? "
            "(This does not delete the NotebookLM notebook) [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return

    if state_manager.delete_course(cid):
        print(f"Deleted '{name}' (ID: {cid}) from local DB.")
    else:
        print(f"Failed to delete '{name}' (ID: {cid}).")


def delete_all_managed_courses(state_manager, assume_yes=False):
    managed = state_manager.get_all_managed_courses()
    if not managed:
        print("No managed courses found in database.")
        return

    if not assume_yes:
        confirm = input(
            f"Delete all {len(managed)} managed courses from local DB? "
            "(This does not delete NotebookLM notebooks) [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Delete-all cancelled.")
            return

    deleted = 0
    for cid, _, _ in managed:
        if state_manager.delete_course(cid):
            deleted += 1
    print(f"Deleted {deleted}/{len(managed)} managed courses from local DB.")


async def delete_courses_flow(state_manager):
    """
    Interactive flow to delete courses.
    """
    managed = list_managed_courses(state_manager)
    if not managed:
        return
    
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
    args = setup_args()

    # Initialize modules
    state_manager = StateManager()

    if args.delete_target and args.delete_all:
        logging.error("Use either --delete or --delete-all, not both.")
        return

    # Direct utility actions
    if args.list_managed_courses:
        list_managed_courses(state_manager)

    if args.delete_target:
        delete_managed_courses(state_manager, args.delete_target, assume_yes=args.yes)

    if args.delete_all:
        delete_all_managed_courses(state_manager, assume_yes=args.yes)

    has_direct_utility_action = args.list_managed_courses or bool(args.delete_target) or args.delete_all
    # Backward compatibility: `-y` alone still means "run sync non-interactively".
    wants_headless_sync_all = args.yes and not has_direct_utility_action and not args.interactive and not args.sync_managed_courses
    has_sync_flag = args.sync_managed_courses or wants_headless_sync_all

    # If only list/delete actions were requested, exit after performing them.
    if has_direct_utility_action and not has_sync_flag and not args.interactive:
        return

    if not CANVAS_KEY:
         logging.error("CANVAS_KEY not set. Please set CANVAS_URL and CANVAS_KEY env vars.")
         return

    canvas_client = CanvasClient(CANVAS_URL, CANVAS_KEY)
    notebook_client = NotebookLMClientWrapper()

    # Check/Force Interactive Mode if no args
    # If non-interactive sync flags are passed, skip the menu unless --interactive is set.
    # Default behavior: If no args, show menu.
    show_menu = args.interactive or (not has_direct_utility_action and not has_sync_flag)

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
                args.sync_managed_courses = False
                # User can still be prompted inside sync unless they passed -y to the script originally
                await sync_courses(canvas_client, state_manager, notebook_client, args)
            elif choice == '2':
                # Sync managed only
                args.sync_managed_courses = True
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
