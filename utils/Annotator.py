#!/usr/bin/env python3
"""
Main Entry Point for Object Detection Annotation Tool

This file imports and runs the main AnnotationGUI application.
All classes have been modularized into separate files in the utils folder:
  - TkTerminalRedirector → utils/TkTerminalRedirector.py
  - TrainingConfigDialog → utils/TrainingConfigDialog.py
  - AnnotationGUI → utils/AnnotationGUI.py
"""

import sys
import os
import tkinter as tk

# Add parent directory to path so utils is recognized as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from utils.AnnotationGUI import AnnotationGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationGUI(root)
    root.mainloop()
