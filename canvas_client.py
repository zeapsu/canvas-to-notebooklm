import os
import requests
import shutil
from canvasapi import Canvas
from typing import List, Dict, Any

class CanvasClient:
    def __init__(self, api_url: str, api_key: str):
        """
        Initialize the Canvas Client.
        :param api_url: Base URL for the Canvas instance.
        :param api_key: API Access Token.
        """
        self.api_url = api_url
        self.api_key = api_key
        self.canvas = Canvas(api_url, api_key)

    def get_active_courses(self) -> List[Any]:
        """
        Retrieve a list of active courses for the current user.
        """
        print(f"Fetching courses from {self.api_url}...")
        try:
            user = self.canvas.get_current_user()
            # Fetch courses with 'term' to filter by active term if needed, or just return all favorites/active
            courses = user.get_courses(enrollment_state='active')
            return list(courses)
        except Exception as e:
            print(f"Error fetching courses: {e}")
            return []

    def get_course_files(self, course_id: int) -> List[Any]:
        """
        Recursively fetch all files for a given course.
        :param course_id: The ID of the course.
        """
        print(f"Fetching files for course {course_id}...")
        try:
            course = self.canvas.get_course(course_id)
            files = course.get_files()
            return list(files)
        except Exception as e:
            print(f"Error fetching files for course {course_id}: {e}")
            return []

    def download_file(self, file_url: str, destination_path: str):
        """
        Download a file from a URL to a local destination.
        """
        print(f"Downloading {file_url} to {destination_path}...")
        try:
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Canvas file URLs from API might require auth headers if not public, 
            # but usually the download_url in the file object includes a verifier or we use the session.
            # safe assumption: use the requests session from canvasapi payload or just a fresh request
            # For simplicity, using a fresh request with the API key in headers if needed, 
            # but often 'url' property in file object works directly.
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with requests.get(file_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(destination_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Downloaded: {destination_path}")
        except Exception as e:
            print(f"Error downloading file {file_url}: {e}")
