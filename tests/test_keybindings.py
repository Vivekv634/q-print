# tests/test_keybindings.py
from server.ui import keybindings


def test_all_shortcuts_are_strings():
    for attr in ("QUIT", "EDIT_COST", "REFRESH_QUEUE", "SHOW_QR_CODE", "FIND_NEARBY_SHOPS"):
        val = getattr(keybindings, attr)
        assert isinstance(val, str), f"{attr} must be a string"
        assert len(val) > 0, f"{attr} must not be empty"


def test_no_duplicate_shortcuts():
    shortcuts = [
        keybindings.QUIT,
        keybindings.EDIT_COST,
        keybindings.REFRESH_QUEUE,
        keybindings.SHOW_QR_CODE,
        keybindings.FIND_NEARBY_SHOPS,
    ]
    assert len(shortcuts) == len(set(shortcuts)), "Duplicate shortcuts detected"
