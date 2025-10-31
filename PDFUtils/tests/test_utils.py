"""Tests for utils helper functions to reach full coverage."""

from __future__ import annotations

import logging

import pytest

from pdfutils import utils


@pytest.mark.timeout(10)
def test_configure_logging_idempotent():
    # Ensure no handlers initially for controlled test
    root = logging.getLogger()
    # Remove existing handlers temporarily
    existing = list(root.handlers)
    for h in existing:
        root.removeHandler(h)

    try:
        utils.configure_logging(level=logging.DEBUG)
        assert root.handlers, "configure_logging should attach at least one handler"

        # Call again – should not duplicate handlers
        before = len(root.handlers)
        utils.configure_logging(level=logging.INFO)
        assert len(root.handlers) == before
    finally:
        # Restore previous handlers
        for h in root.handlers:
            root.removeHandler(h)
        for h in existing:
            root.addHandler(h)


@pytest.mark.timeout(10)
def test_find_ghostscript_command_env(monkeypatch):
    monkeypatch.setenv("GS_PROG", "mygs")

    # Case 1: env variable resolves via which
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/usr/bin/mygs" if x == "mygs" else None)
    assert utils.find_ghostscript_command() == "mygs"

    # Case 2: env variable doesn't resolve but candidate does
    monkeypatch.setenv("GS_PROG", "nonexistent")

    def fake_which(name: str):
        if name == "gs":
            return "/usr/bin/gs"
        return None

    monkeypatch.setattr(utils.shutil, "which", fake_which)
    assert utils.find_ghostscript_command() == "gs"

    # Case 3: nothing found returns None
    monkeypatch.setenv("GS_PROG", "none")
    monkeypatch.setattr(utils.shutil, "which", lambda x: None)
    # Also mock the os.listdir and os.path.exists to prevent finding Ghostscript in common paths
    monkeypatch.setattr(utils.os, "listdir", lambda x: [])
    monkeypatch.setattr(utils.os.path, "exists", lambda x: False)
    assert utils.find_ghostscript_command() is None
