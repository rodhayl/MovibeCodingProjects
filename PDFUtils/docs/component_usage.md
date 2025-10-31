# Component Usage Patterns

This document describes the standard usage patterns for the UI components in the PDFUtils GUI.

## Overview

The PDFUtils GUI uses a component-based architecture with reusable UI components. All components are located in the `pdfutils.gui.components` package.

## Available Components

### FileSelector

A component for selecting files with preview capabilities.

**Usage:**
```python
from pdfutils.gui.components import FileSelector, SPACING

# Basic file selector (single file)
file_selector = FileSelector(
    parent,
    file_types=[("PDF files", "*.pdf")],
    label_text="PDF file:",
    multiple=False,
    show_preview=True,
)

# Multiple file selector
file_selector = FileSelector(
    parent,
    file_types=[("PDF files", "*.pdf"), ("All files", "*.*")],
    label_text="Source files:",
    multiple=True,
    show_preview=False,
)

# Grid placement
file_selector.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])

# Methods
files = file_selector.get_files()  # Get selected files (list)
file = file_selector.get_file()    # Get single selected file (string)
file_selector.set_files([])        # Clear selected files
```

### OutputFileSelector

A component for selecting output file paths.

**Usage:**
```python
from pdfutils.gui.components import OutputFileSelector, SPACING

output_selector = OutputFileSelector(
    parent,
    file_types=[("PDF files", "*.pdf")],
    label_text="Output file:",
    default_extension=".pdf",
)

# Grid placement
output_selector.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])

# Methods
path = output_selector.get_path()  # Get selected path
output_selector.set_path("")       # Clear selected path
```

### ResponsiveSection

A collapsible section container with title.

**Usage:**
```python
from pdfutils.gui.components import ResponsiveSection, SPACING

# Create section
sec = ResponsiveSection(parent, title="Section Title", collapsible=True)

# Grid placement
sec.grid(row=0, column=0, sticky="ew", pady=SPACING["md"])

# Access content frame
content_frame = sec.content_frame
```

### ProgressTracker

A component for tracking progress with status messages.

**Usage:**
```python
from pdfutils.gui.components import ProgressTracker, SPACING

progress_tracker = ProgressTracker(parent)

# Grid placement
progress_tracker.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])

# Methods
progress_tracker.update_progress(50, "Processing...")  # Update progress
progress_tracker.reset()                              # Reset to 0
```

### TabContentFrame

Base class for tab content with scrollable layout.

**Usage:**
```python
from pdfutils.gui.components import TabContentFrame

class MyTab(TabContentFrame):
    def __init__(self, master):
        super().__init__(master)
        # Add content to self.scrollable_frame
```

## Base Classes for Tabs

### WorkerTab

Base class for tabs that perform background operations.

**Features:**
- Automatic UI state management
- Background threading
- Progress tracking
- Error handling

**Usage:**
```python
from pdfutils.tabs.base_tab import WorkerTab
from pdfutils.gui.components import TabContentFrame

class MyTab(WorkerTab, TabContentFrame):
    def __init__(self, master, app):
        WorkerTab.__init__(self, master, app)
        TabContentFrame.__init__(self, master)
        
        # Set up action button reference for UI state management
        self.action_button = ttk.Button(...)
        
    def _on_action(self):
        # Use worker pattern
        self._run_worker(lambda: self._worker_function(), "Operation completed")
        
    def _worker_function(self):
        # Perform background operation
        pass
```

### BaseTab

Base class with common tab functionality.

**Features:**
- Notification system
- Status updates
- Progress tracking
- Tab lifecycle management

## Constants

The `SPACING` dictionary provides consistent spacing values:
- `SPACING["xs"]` - Extra small spacing
- `SPACING["sm"]` - Small spacing
- `SPACING["md"]` - Medium spacing
- `SPACING["lg"]` - Large spacing
- `SPACING["xl"]` - Extra large spacing

## Best Practices

1. **Import Pattern:**
   ```python
   from pdfutils.gui.components import (
       TabContentFrame,
       ResponsiveSection,
       FileSelector,
       OutputFileSelector,
       ProgressTracker,
       SPACING,
   )
   ```

2. **Grid Layout:**
   - Use `SPACING` constants for consistent padding and margins
   - Place sections in consecutive rows starting from row 0
   - Use `sticky="ew"` for horizontal expansion

3. **Background Operations:**
   - Use `WorkerTab` base class for tabs with background operations
   - Implement worker functions separately from UI event handlers
   - Use `_run_worker()` method for automatic threading and error handling

4. **Component Reusability:**
   - Components are designed to be reusable across different tabs
   - Components handle their own state management
   - Components provide consistent APIs for getting/setting values