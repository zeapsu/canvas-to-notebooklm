import sqlite3
import os
from datetime import datetime

class StateManager:
    def __init__(self, db_path="state.db"):
        """
        Initialize the State Manager with a SQLite database.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Initialize the database schema.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT,
                notebook_lm_id TEXT,
                last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                course_id TEXT,
                file_name TEXT,
                upload_status TEXT DEFAULT 'pending',
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(course_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_course_notebook_id(self, course_id):
        """
        Retrieve the NotebookLM ID for a given course.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT notebook_lm_id FROM courses WHERE course_id = ?', (course_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_course_notebook_id(self, course_id, notebook_id, course_name=None):
        """
        Save or update the NotebookLM ID for a course.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO courses (course_id, notebook_lm_id, course_name, last_synced_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(course_id) DO UPDATE SET 
                notebook_lm_id=excluded.notebook_lm_id,
                course_name=coalesce(excluded.course_name, courses.course_name),
                last_synced_at=excluded.last_synced_at
        ''', (course_id, notebook_id, course_name, datetime.now()))
        conn.commit()
        conn.close()

    def get_all_managed_courses(self):
        """
        Retrieve all courses currently managed in the database.
        Returns a list of tuples: (course_id, course_name, notebook_lm_id)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT course_id, course_name, notebook_lm_id FROM courses')
        results = cursor.fetchall()
        conn.close()
        return results

    def delete_course(self, course_id):
        """
        Remove a course and its associated files from the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Delete associated files first (foreign key constraint usually handles this but good to be explicit/safe)
            cursor.execute('DELETE FROM files WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM courses WHERE course_id = ?', (course_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting course {course_id}: {e}")
            return False
        finally:
            conn.close()

    def is_file_processed(self, file_id):
        """
        Check if a file has already been successfully uploaded.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM files WHERE file_id = ? AND upload_status = 'uploaded'", (file_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_file_processed(self, file_id, course_id, file_name):
        """
        Mark a file as uploaded.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO files (file_id, course_id, file_name, upload_status, last_updated_at)
            VALUES (?, ?, ?, 'uploaded', ?)
            ON CONFLICT(file_id) DO UPDATE SET 
                upload_status='uploaded',
                last_updated_at=excluded.last_updated_at
        ''', (file_id, course_id, file_name, datetime.now()))
        conn.commit()
        conn.close()
