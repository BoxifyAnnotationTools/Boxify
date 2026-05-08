"""
Training and inference functions with argparse
"""
import os
import shutil
import numpy as np
import torch
import gc
import argparse

try:
    from ultralytics import YOLO
except Exception as e:
    YOLO = None
    print("[INFO] ultralytics not installed. Training won't work.", e)


# ─────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="YOLO Training Script")

    parser.add_argument("--dataset_root",   type=str, required=True,
                        help="Root folder dataset (contains images/ and labels/)")
    parser.add_argument("--images_folder",  type=str, required=True,
                        help="Folder containing training images")
    parser.add_argument("--classlist",      nargs="+", required=True,
                        help="Class names, e.g.: --classlist person car motor")
    parser.add_argument("--model_path",     type=str, default="best.pt",
                        help="Path to save / load YOLO model")
    parser.add_argument("--model_folder",   type=str, default="runs",
                        help="Folder to store training results")
    parser.add_argument("--model_type",     type=str, default="detect",
                        choices=["detect", "seg"],
                        help="Task type: 'detect' or 'seg'")
    parser.add_argument("--base_model",     type=str, default=None,
                        help="Base pretrained model to use when no existing model found "
                             "(e.g. yolo11s.pt, yolov8m-seg.pt). "
                             "Overrides the built-in default.")
    parser.add_argument("--epochs",         type=int, default=10,
                        help="Number of training epochs")
    parser.add_argument("--batch",          type=int, default=4,
                        help="Training batch size")
    parser.add_argument("--imgsz",          type=int, default=640,
                        help="Input image size (pixels, multiple of 32)")
    parser.add_argument("--ratio",          type=float, default=0.7,
                        help="Train/val split ratio")

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────
# Dataset split
# ─────────────────────────────────────────────────────────────────

def split_train_val(root, ratio=0.7):
    """Split dataset into train and validation sets."""
    images_dir = os.path.join(root, "images")
    labels_dir = os.path.join(root, "labels")

    imgs = [f for f in os.listdir(images_dir)
            if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if len(imgs) < 2:
        print("[WARN] Not enough images to split train/val.")
        return None, None

    np.random.shuffle(imgs)
    train_count = int(len(imgs) * ratio)
    train_imgs  = imgs[:train_count]
    val_imgs    = imgs[train_count:]

    train_img_dir = os.path.join(root, "train/images")
    train_lbl_dir = os.path.join(root, "train/labels")
    val_img_dir   = os.path.join(root, "val/images")
    val_lbl_dir   = os.path.join(root, "val/labels")

    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    for img in train_imgs:
        base = os.path.splitext(img)[0]
        shutil.copy2(os.path.join(images_dir, img), os.path.join(train_img_dir, img))
        lbl = base + ".txt"
        if os.path.exists(os.path.join(labels_dir, lbl)):
            shutil.copy2(os.path.join(labels_dir, lbl), os.path.join(train_lbl_dir, lbl))

    for img in val_imgs:
        base = os.path.splitext(img)[0]
        shutil.copy2(os.path.join(images_dir, img), os.path.join(val_img_dir, img))
        lbl = base + ".txt"
        if os.path.exists(os.path.join(labels_dir, lbl)):
            shutil.copy2(os.path.join(labels_dir, lbl), os.path.join(val_lbl_dir, lbl))

    return train_img_dir, val_img_dir


# ─────────────────────────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────────────────────────

def train_model(args):
    """Train YOLO model dari argparse inputs."""

    inference_images = args.images_folder
    inference_root   = args.dataset_root
    CLASSLIST        = args.classlist
    model_path       = args.model_path
    model_folder     = args.model_folder
    model_type       = args.model_type   # "detect" | "seg"

    # Minimum image check
    images_infer = [f for f in os.listdir(inference_images)
                    if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if len(images_infer) < 10:
        print("[INFO] Not enough images to train (min 10 required).")
        return

    # Dataset split
    print("[INFO] Splitting dataset...")
    train_dir, val_dir = split_train_val(inference_root, ratio=args.ratio)
    if train_dir is None or val_dir is None:
        print("[ERROR] Dataset split failed.")
        return

    # Write data.yaml
    yaml_path = os.path.join(inference_root, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"train: {os.path.abspath(train_dir)}\n")
        f.write(f"val:   {os.path.abspath(val_dir)}\n")
        f.write(f"nc:    {len(CLASSLIST)}\n")
        f.write("names: [" + ", ".join([f"'{n}'" for n in CLASSLIST]) + "]\n")
    print("[INFO] YAML created:", yaml_path)

    # ── Tentukan model yang akan dipakai ────────────────────────
    #   Prioritas:
    #     1. existing model_path  → lanjut training (continue)
    #     2. --base_model dari dialog  → pretrained pilihan user
    #     3. fallback default built-in
    default_base = "yolo11s-seg.pt" if model_type == "seg" else "yolo11s.pt"

    if os.path.exists(model_path):
        init_model = model_path
        print("\n" + "=" * 70)
        print("[INFO] CONTINUING FROM EXISTING CUSTOM MODEL")
        print(f"  Path       : {model_path}")
        print(f"  Task       : {'🔷 SEGMENTATION' if model_type == 'seg' else '📦 DETECTION'}")
        print("=" * 70 + "\n")

    elif args.base_model:
        init_model = args.base_model
        print("\n" + "=" * 70)
        print("[INFO] STARTING FROM USER-SELECTED BASE MODEL")
        print(f"  Base model : {args.base_model}")
        print(f"  Task       : {'🔷 SEGMENTATION' if model_type == 'seg' else '📦 DETECTION'}")
        print("=" * 70 + "\n")

    else:
        init_model = default_base
        print("\n" + "=" * 70)
        print("[INFO] NO EXISTING MODEL — using built-in default")
        print(f"  Base model : {default_base}")
        print(f"  Task       : {'🔷 SEGMENTATION' if model_type == 'seg' else '📦 DETECTION'}")
        print("=" * 70 + "\n")

    # ── Training ─────────────────────────────────────────────────
    print(f"[DEBUG] data : {yaml_path}, project : {model_folder}, len train : {len(os.listdir(train_dir))}, len val : {len(os.listdir(val_dir))}")
    try:
        model = YOLO(init_model)
        print("[INFO] Starting training...")

        model.train(
            data=yaml_path,
            epochs=args.epochs,
            imgsz=args.imgsz,           # ← dari argparse, bukan hardcoded
            batch=args.batch,
            optimizer="auto",
            project=model_folder,
            name="train_run",
            exist_ok=True,
            device=0,
            amp=False,
            workers=1
        )

        model.save(model_path)
        del model
        print(f"[INFO] Training finished. Model saved to: {model_path}")

    except Exception as e:
        print("[ERROR] Training failed:", e)

    # ── Bersihkan folder sementara ───────────────────────────────
    try:
        print("[INFO] Cleaning temporary train/val folders...")
        shutil.rmtree(os.path.join(inference_root, "train"))
        shutil.rmtree(os.path.join(inference_root, "val"))
        print("[INFO] train/ & val/ removed.")
    except Exception as e:
        print("[WARN] Failed to delete train/val folders:", e)

    torch.cuda.empty_cache()
    gc.collect()

# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    train_model(args)