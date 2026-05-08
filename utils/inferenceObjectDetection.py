"""
Training and inference functions
"""
import os
import shutil
import numpy as np
import torch
import gc
import cv2

from .config import model_path, CLASSLIST, state, input_folder

try:
    from ultralytics import YOLO
except Exception as e:
    YOLO = None
    print("[INFO] ultralytics not installed. Training won't work.", e)

def inference_current(images, current_index, conf=0.3):
    """Run inference on current image"""
    if not os.path.exists(model_path):
        print("[INFO] Model assistant does not exist.")
        return

    img_path = os.path.join(input_folder, images[current_index])
    orig_img = cv2.imread(img_path)

    # Catatan Performa: Idealnya 'model = YOLO(...)' diinisialisasi sekali saja 
    # di luar fungsi agar tidak terus-menerus memuat ulang weights ke VRAM.
    model = YOLO(model_path)

    with torch.no_grad():
        results = model.predict(orig_img, conf=conf, iou=0.3)

    pred_data = []
    is_polygon = False

    for r in results:
        # --- 1. EKSTRAKSI POLYGON (Jika model mendukung segmentasi) ---
        if hasattr(r, 'masks') and r.masks is not None:
            is_polygon = True
            
            for i, poly in enumerate(r.masks.xy):
                cls_idx = int(r.boxes.cls[i].item())
                cls_name = CLASSLIST[cls_idx] if cls_idx < len(CLASSLIST) else str(cls_idx)

                # PERBAIKAN: 
                # Simpan sebagai Tuple (points_orig, cls_name)
                # poly.tolist() mengubah numpy array murni menjadi struktur list Python
                # TANPA scaling, karena update_display sudah melakukan scaling untuk poligon.
                pred_data.append((poly.tolist(), cls_name))
                
        # --- 2. EKSTRAKSI BBOX (Fallback jika tidak ada segmentasi) ---
        elif hasattr(r, 'boxes') and r.boxes is not None:
            for box in r.boxes:
                x1 = int(box.xyxy[0, 0].item())
                y1 = int(box.xyxy[0, 1].item())
                x2 = int(box.xyxy[0, 2].item())
                y2 = int(box.xyxy[0, 3].item())
                cls_idx = int(box.cls[0].item())
                cls_name = CLASSLIST[cls_idx] if cls_idx < len(CLASSLIST) else str(cls_idx)

                # Store bboxes in ORIGINAL image coordinates (no display scaling)
                pred_data.append([
                    int(round(x1)),
                    int(round(y1)),
                    int(round(x2)),
                    int(round(y2)),
                    cls_name
                ])

    # --- 3. UPDATE STATE ---
    if is_polygon:
        state.polygons = pred_data
        print(f"[INFO] Inference saved. {len(pred_data)} POLYGONS updated.")
    else:
        state.bboxes = pred_data
        print(f"[INFO] Inference saved. {len(pred_data)} BBOXES updated.")

    # --- 4. CLEANUP MEMORY ---
    del results
    torch.cuda.empty_cache()
    gc.collect()