from pathlib import Path

from state_manager import StateManager


def test_course_mapping_round_trip(tmp_path: Path):
    db_path = tmp_path / "state_test.db"
    sm = StateManager(str(db_path))

    sm.set_course_notebook_id("course-1", "nb-1", "Physics")
    assert sm.get_course_notebook_id("course-1") == "nb-1"

    managed = sm.get_all_managed_courses()
    assert len(managed) == 1
    assert managed[0][0] == "course-1"
    assert managed[0][1] == "Physics"
    assert managed[0][2] == "nb-1"


def test_file_processed_tracking(tmp_path: Path):
    db_path = tmp_path / "state_test.db"
    sm = StateManager(str(db_path))

    assert sm.is_file_processed("file-1") is False
    sm.mark_file_processed("file-1", "course-1", "lecture1.pdf")
    assert sm.is_file_processed("file-1") is True


def test_delete_course_removes_related_files(tmp_path: Path):
    db_path = tmp_path / "state_test.db"
    sm = StateManager(str(db_path))

    sm.set_course_notebook_id("course-1", "nb-1", "Physics")
    sm.mark_file_processed("file-1", "course-1", "lecture1.pdf")

    assert sm.delete_course("course-1") is True
    assert sm.get_course_notebook_id("course-1") is None
    assert sm.is_file_processed("file-1") is False
