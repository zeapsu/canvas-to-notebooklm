import asyncio
from notebooklm import NotebookLMClient
from typing import Optional

import logging

class NotebookLMClientWrapper: # Renamed to avoid confusion with the library class
    def __init__(self, headless: bool = True):
        """
        Initialize the NotebookLM Client Wrapper.
        """
        self.headless = headless
        self.client: Optional[NotebookLMClient] = None

    async def _get_client(self) -> NotebookLMClient:
        if not self.client:
            try:
                # Try to load from default storage path
                self.client = await NotebookLMClient.from_storage()
            except Exception as e:
                logging.error(f"Error loading NotebookLM client from storage: {e}")
                print("Please run the login script first or ensure you have authenticated.")
                raise e
        return self.client

    async def login(self):
        """
        Perform login to Google/NotebookLM.
        This uses Playwright to interactive login and save state.
        """
        logging.info("Logging in to NotebookLM...")
        # This functionality is usually handled by the library's CLI or a separate script.
        # For this wrapper, we assume the user might need to run a manual step via CLI: 
        # `notebooklm login`
        # But we can try to automate if needed.
        # For now, we'll guide the user.
        print("To login, please run 'notebooklm login' in your terminal.")

    async def create_notebook(self, title: str) -> str:
        """
        Create a new notebook with the given title.
        :return: The ID of the created notebook.
        """
        logging.info(f"Creating notebook: {title}")
        client = await self._get_client()
        async with client:
            notebook = await client.notebooks.create(title=title)
            return notebook.id

    async def upload_source(self, notebook_id: str, file_path: str):
        """
        Upload a file to the specified notebook.
        """
        logging.info(f"Uploading {file_path} to notebook {notebook_id}...")
        client = await self._get_client()
        async with client:
            # add_file returns the Source object or ID? 
            # Looking at library code (via inspection earlier): SourceAPI.add_file returns 'Source' object usually.
            # verify call: await client.sources.add_file(notebook_id, file_path)
            source = await client.sources.add_file(notebook_id, file_path)
            
            # If add_file returns a Source object, we can get its ID.
            source_id = getattr(source, 'id', None)
            
            if source_id:
                 # Wait for processing
                try:
                    await client.sources.wait_for_sources(notebook_id, source_ids=[source_id])
                except Exception as e:
                    logging.warning(f"Error waiting for source processing: {e}")
            else:
                logging.warning("Could not determine source ID to wait for processing.")
