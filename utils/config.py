"""
Configuration file for annotation tool - UPDATED VERSION
Uses ClassManager for dynamic class handling
"""

import os
from .class_manager import ClassManager
import tkinter as tk
from tkinter import filedialog


# ======== ERROR DIALOG HELPER ========
def show_error_dialog(title, message):
    """Show error dialog and wait for user to close it before continuing"""
    root = tk.Tk()
    root.withdraw()
    from tkinter import messagebox
    
    # Show error dialog - this will block until user clicks OK
    messagebox.showerror(title, message, parent=root)
    
    # Make sure the dialog is processed
    root.update()
    root.destroy()

# ======== BASE DIRECTORY ========
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


# ======== PREPARE DATASET ROOT DIRECTORY ========
# All datasets must be placed inside this directory
datasets_root = os.path.join(BASE_DIR, "datasetsInput")
os.makedirs(datasets_root, exist_ok=True)


# ======== SELECT INPUT FOLDER (RESTRICTED TO DATASETS ROOT) ========
_root = tk.Tk()
_root.withdraw()  # Hide the main Tkinter window

input_folder = filedialog.askdirectory(
    title="Select Dataset Folder",
    initialdir=datasets_root
)

_root.destroy()


# ======== VALIDATION ========

def validate_folder(folder):
    if not folder:
        show_error_dialog(
            "No Folder Selected",
            "You didn't select any dataset folder."
        )
        return False

    folder = os.path.realpath(folder)
    root = os.path.realpath(datasets_root)

    try:
        common_path = os.path.commonpath([folder, root])
    except ValueError:
        show_error_dialog(
            "Invalid Folder",
            "Selected folder path is not valid."
        )
        return False

    if common_path != root:
        show_error_dialog(
            "Access Denied",
            "Folder must be inside 'datasetsInput'."
        )
        return False

    image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")

    image_files = [
        f for f in os.listdir(folder)
        if f.lower().endswith(image_extensions)
    ]

    if len(image_files) == 0:
        show_error_dialog(
            "Empty Dataset",
            "No images found in selected folder."
        )
        return False

    return True

# ======== VALIDATE SELECTED FOLDER ========
if not validate_folder(input_folder):
    raise SystemExit("Invalid folder selected. Exiting.")


# ======== WORKSPACE CONFIGURATION ========
folder_name = os.path.basename(os.path.normpath(input_folder))

# Default workspace name
workspaceName = folder_name

# Remove suffix like "-1", "-2", etc. if present
if "-" in folder_name:
    base, suffix = folder_name.rsplit("-", 1)
    if suffix.isdigit():
        workspaceName = base


# ======== OUTPUT AND MODEL PATHS ========
output_folder = os.path.join(BASE_DIR, "output", workspaceName)

inference_root = os.path.join(BASE_DIR, "inference", workspaceName)
inference_images = os.path.join(inference_root, "images")
inference_labels = os.path.join(inference_root, "labels")

model_folder = os.path.join(BASE_DIR, "models", workspaceName)
model_path = os.path.join(model_folder, "modelAssistant.pt")
export_model_folder = os.path.join(BASE_DIR, "export model", workspaceName)
export_dataset_folder = os.path.join(BASE_DIR, "export dataset", workspaceName)


# ======== CREATE REQUIRED DIRECTORIES ========
for d in [output_folder, inference_images, inference_labels, model_folder, export_model_folder, export_dataset_folder]:
    os.makedirs(d, exist_ok=True)


# ======== CLASS CONFIGURATION ========
# Initialize ClassManager for the current workspace
class_manager = ClassManager(workspaceName)

# Load class list and color palette
CLASSLIST = class_manager.get_classes()
colorsPalette = class_manager.get_colors()

# Ensure at least one default class exists
if not CLASSLIST:
    print("[Config] No classes found. Using default class 'Object'")
    CLASSLIST = ["Object"]
    class_manager.add_class("Object")
    colorsPalette = class_manager.get_colors()


# ======== UI SETTINGS ========
CLASS_HEIGHT = 35
CLASS_WINDOW_W = 220
CLASS_WINDOW_H = 360


# ======== APPLICATION STATE ========
class State:
    def __init__(self):
        # Navigation
        self.current_index = 0

        # Annotation data
        self.bboxes = []
        self.polygons = []  # Format: [points, class, type]

        # History (for repeat functionality)
        self.prev_bboxes = []
        self.prev_polygons = []

        # Selection
        self.selected_bbox = None
        self.selected_polygon = None
        self.selected_polygon_point = None

        # Interaction flags
        self.drawing = False
        self.moving = False
        self.resizing = False
        self.resize_mode = None
        self.force_new_bbox = False

        # Mouse position
        self.ix, self.iy = -1, -1

        # Display scaling
        self.display_scale = 1.0
        self.orig_width = None
        self.orig_height = None
        self.display_width = None
        self.display_height = None

        # Frame data
        self.frame = None
        self.orig_shape = None

        # UI state
        self.scroll_offset = 0
        self.show_bbox_text = True

        # Training state
        self.training_running = False
        self.training_process = None

        # Automation
        self.automated_annotation = False
        self.auto_annotation = False

        # Class handling
        self.current_class = CLASSLIST[0] if CLASSLIST else "Object"
        self.visible_class = {cls: True for cls in CLASSLIST}

        # ===== Polygon Annotation Support =====
        self.annotation_mode = "bbox"  # Options: "bbox" or "polygon"
        self.polygon_points_preview = []  # Points before finalizing polygon
        self.polygon_editing_mode = False


# Global state instance
state = State()