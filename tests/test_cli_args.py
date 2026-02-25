from main import setup_args


def test_sync_managed_aliases_are_equivalent():
    args = setup_args(["--sync-managed-courses"])
    assert args.sync_managed_courses is True

    alias_args = setup_args(["--update-existing"])
    assert alias_args.sync_managed_courses is True


def test_list_managed_aliases_are_equivalent():
    args = setup_args(["--list-managed-courses"])
    assert args.list_managed_courses is True

    alias_args = setup_args(["--list-managed"])
    assert alias_args.list_managed_courses is True


def test_delete_target_parses_value():
    args = setup_args(["--delete", "1618718"])
    assert args.delete_target == "1618718"
