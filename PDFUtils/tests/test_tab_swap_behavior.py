import tkinter as tk

import pytest


@pytest.mark.gui
def test_placeholder_swap_keeps_order_and_loads_first_tab():
    try:
        from pdfutils.responsive_main import PDFUtilsApp
    except Exception as e:  # pragma: no cover - import issues
        pytest.skip(f"Cannot import app: {e}")

    # Create a root window; on headless systems this may fail
    try:
        root = tk.Tk()
    except Exception as e:  # pragma: no cover - headless fallback
        pytest.skip(f"Tk not available: {e}")

    app = PDFUtilsApp(root)

    # Record initial notebook tab titles (all placeholders)
    initial_titles = [app.notebook.tab(t, "text") for t in app.notebook.tabs()]
    assert initial_titles[0] == "Merge"

    # Trigger lazy load of the first tab and verify state
    app._load_first_tab()

    # Titles remain the same and in the same order
    after_titles = [app.notebook.tab(t, "text") for t in app.notebook.tabs()]
    assert after_titles == initial_titles

    # Exactly one real tab is loaded after first activation
    assert len(app.tabs) == 1

    # Selected tab is still "Merge"
    current = app.notebook.select()
    assert app.notebook.tab(current, "text") == "Merge"

    root.destroy()
