"""
File handling functions for VOC and YOLO formats
Supports both bounding boxes and polygons
"""
import os
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom
from .config import output_folder, inference_labels, inference_images, input_folder, CLASSLIST, state

def prettify_xml(elem):
    """Convert XML to pretty-printed string"""
    return minidom.parseString(ET.tostring(elem)).toprettyxml(indent="   ")

def save_pascal_voc(img_name, img_shape):
    """Save annotations in Pascal VOC format (bboxes and polygons)"""
    xml_path = os.path.join(output_folder, os.path.splitext(img_name)[0] + ".xml")
    ann = ET.Element("annotation")
    ET.SubElement(ann, "folder").text = "dataset"
    ET.SubElement(ann, "filename").text = img_name
    size = ET.SubElement(ann, "size")
    ET.SubElement(size, "width").text = str(img_shape[1])
    ET.SubElement(size, "height").text = str(img_shape[0])
    ET.SubElement(size, "depth").text = str(img_shape[2] if len(img_shape) > 2 else 3)
    
    # Save bboxes
    for bbox in state.bboxes:
        # `state.bboxes` are stored in ORIGINAL image coordinates
        x1 = int(round(bbox[0]))
        y1 = int(round(bbox[1]))
        x2 = int(round(bbox[2]))
        y2 = int(round(bbox[3]))
        cls = bbox[4]
        obj = ET.SubElement(ann, "object")
        ET.SubElement(obj, "name").text = cls
        ET.SubElement(obj, "type").text = "bbox"
        bnd = ET.SubElement(obj, "bndbox")
        ET.SubElement(bnd, "xmin").text = str(max(0, x1))
        ET.SubElement(bnd, "ymin").text = str(max(0, y1))
        ET.SubElement(bnd, "xmax").text = str(max(0, x2))
        ET.SubElement(bnd, "ymax").text = str(max(0, y2))
    
    # Save polygons
    for polygon_data in state.polygons:
        points_orig = polygon_data[0]  # Points already in ORIGINAL coordinates (stored as float)
        cls = polygon_data[1]
        
        obj = ET.SubElement(ann, "object")
        ET.SubElement(obj, "name").text = cls
        ET.SubElement(obj, "type").text = "polygon"
        
        # Points are already in original coordinates, just save directly
        poly_elem = ET.SubElement(obj, "polygon")
        for x, y in points_orig:
            # Round to int for storage
            x_int = int(round(x))
            y_int = int(round(y))
            pt = ET.SubElement(poly_elem, "point")
            ET.SubElement(pt, "x").text = str(max(0, x_int))
            ET.SubElement(pt, "y").text = str(max(0, y_int))
    
    with open(xml_path, "w") as f:
        f.write(prettify_xml(ann))
    print(f"[INFO] Saved VOC: {xml_path}")

def save_yolo_label_and_image(img_name, orig_img, classList):
    """
    Save YOLO format labels (supports both detection and segmentation)
    - If ONLY bboxes: saved in detection format (class_id cx cy width height)
    - If polygons exist: ALL annotations saved in segmentation format
      (including bboxes converted to polygon format)
    """
    base = os.path.splitext(img_name)[0]
    label_path = os.path.join(inference_labels, base + ".txt")
    dest_img = os.path.join(inference_images, img_name)
    h, w, c = orig_img
    lines = []

    # Check if dataset has polygons
    has_polygons = len(state.polygons) > 0

    if has_polygons:
        print(f"[FILE_HANDLER] Dataset has polygons - using segmentation format for all annotations")
        
        # Convert bboxes (stored in ORIGINAL coordinates) to polygon format
        for bbox in state.bboxes:
            x1, y1, x2, y2, cls = bbox

            if cls not in classList:
                continue

            idx = classList.index(cls)

            # Coordinates already in original image scale
            x1_orig = x1
            y1_orig = y1
            x2_orig = x2
            y2_orig = y2

            # Create 4-point polygon from bbox corners
            bbox_polygon_points = [
                (x1_orig, y1_orig),  # top-left
                (x2_orig, y1_orig),  # top-right
                (x2_orig, y2_orig),  # bottom-right
                (x1_orig, y2_orig),  # bottom-left
            ]

            # Normalize to 0-1 range and format
            normalized_points = []
            for x, y in bbox_polygon_points:
                x_norm = max(0, min(1, x / w))
                y_norm = max(0, min(1, y / h))
                normalized_points.append(f"{x_norm:.6f} {y_norm:.6f}")

            # YOLO segmentation format
            line = f"{idx} " + " ".join(normalized_points)
            lines.append(line)
        
        # Save polygons in YOLO segmentation format
        for polygon_data in state.polygons:
            points_orig = polygon_data[0]  # Points already in ORIGINAL coordinates (stored as float)
            cls = polygon_data[1]
            
            if cls not in classList:
                continue
            
            idx = classList.index(cls)
            
            # Normalize points to 0-1 range (points already in original scale)
            normalized_points = []
            for x, y in points_orig:
                x_norm = max(0, min(1, x / w))
                y_norm = max(0, min(1, y / h))
                normalized_points.append(f"{x_norm:.6f} {y_norm:.6f}")
            
            # YOLO segmentation format
            if normalized_points:
                line = f"{idx} " + " ".join(normalized_points)
                lines.append(line)
                print(f"[FILE_HANDLER] Saved polygon segment: {cls} with {len(normalized_points)} points")

    else:
        # Detection format only (no polygons)
        for bbox in state.bboxes:
            x1, y1, x2, y2, cls = bbox

            if cls not in classList:
                continue

            idx = classList.index(cls)

            # Coordinates already in original image scale
            x1_orig = x1
            y1_orig = y1
            x2_orig = x2
            y2_orig = y2

            # Normalize to 0-1 range
            bw = (x2_orig - x1_orig) / w
            bh = (y2_orig - y1_orig) / h
            cx = (x1_orig + x2_orig) / 2 / w
            cy = (y1_orig + y2_orig) / 2 / h

            lines.append(f"{idx} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

    with open(label_path, "w") as f:
        f.write("\n".join(lines))

    shutil.copy2(os.path.join(input_folder, img_name), dest_img)
    print(f"[INFO] Saved YOLO label: {label_path} ({len(lines)} annotations)")


def load_annotation_local(img_name_local):
    """Load annotations from VOC XML file (both bboxes and polygons)
    Supports multiple formats:
    - Our format: <type>polygon</type> with <point><x/><y/></point>
    - Roboflow format: <polygon><x1/><y1/><x2/><y2/>... (no <type> element)
    """
    xml_path = os.path.join(output_folder, os.path.splitext(img_name_local)[0] + ".xml")
    if not os.path.exists(xml_path):
        return [], []  # Return empty bboxes and polygons
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    boxes = []
    polygons = []
    
    for obj in root.findall("object"):
        cls = obj.find("name").text
        
        # ===== CHECK FOR POLYGON FIRST (both formats) =====
        poly_elem = obj.find("polygon")
        is_polygon = False
        points = []
        
        if poly_elem is not None:
            # Try our format first: <point><x/><y/></point>
            point_elems = poly_elem.findall("point")
            if point_elems:
                for point_elem in point_elems:
                    x = float(point_elem.find("x").text)
                    y = float(point_elem.find("y").text)
                    # Store in ORIGINAL coordinates as float (no scale conversion, no rounding)
                    points.append((x, y))
                is_polygon = len(points) >= 3
                if is_polygon:
                    print(f"[FILE_HANDLER] Loaded polygon (our format): {cls} with {len(points)} points")
            
            # Try Roboflow format: <x1/><y1/><x2/><y2/>... <xN/><yN/>
            if not is_polygon:
                roboflow_points = []
                i = 1
                while True:
                    xi_elem = poly_elem.find(f"x{i}")
                    yi_elem = poly_elem.find(f"y{i}")
                    if xi_elem is None or yi_elem is None:
                        break
                    x = float(xi_elem.text)
                    y = float(yi_elem.text)
                    # Store in ORIGINAL coordinates as float (no scale conversion)
                    roboflow_points.append((x, y))
                    i += 1
                
                if len(roboflow_points) >= 3:
                    points = roboflow_points
                    is_polygon = True
                    print(f"[FILE_HANDLER] Loaded polygon (Roboflow format): {cls} with {len(points)} points")
        
        # Add as polygon if we found valid points
        if is_polygon:
            polygons.append([points, cls])  # [points_list, class_name]
        else:
            # ===== ELSE LOAD AS BBOX =====
            bb = obj.find("bndbox")
            if bb is not None:
                x1 = int(float(bb.find("xmin").text))
                y1 = int(float(bb.find("ymin").text))
                x2 = int(float(bb.find("xmax").text))
                y2 = int(float(bb.find("ymax").text))
                # Store as ORIGINAL coordinates (no scaling)
                boxes.append([
                    int(round(x1)),
                    int(round(y1)),
                    int(round(x2)),
                    int(round(y2)),
                    cls
                ])
                print(f"[FILE_HANDLER] Loaded bbox: {cls}")
    
    print(f"[FILE_HANDLER] Loaded {len(boxes)} bboxes, {len(polygons)} polygons from {img_name_local}")
    return boxes, polygons


def detect_dataset_has_polygons():
    """
    Check if dataset has any polygon annotations
    Returns: True if any polygon found, False if only bboxes
    """
    if not os.path.exists(output_folder):
        return False
    
    xml_files = [f for f in os.listdir(output_folder) if f.endswith('.xml')]
    
    if not xml_files:
        return False
    
    # Check first 10 XML files to determine annotation type
    for xml_file in xml_files[:10]:
        xml_path = os.path.join(output_folder, xml_file)
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for obj in root.findall("object"):
                # Check if has <type>polygon</type>
                obj_type = obj.find("type")
                if obj_type is not None and obj_type.text == "polygon":
                    print(f"[TRAINING] Detected polygon annotations in dataset")
                    return True
                
                # Check if has Roboflow format polygon
                poly_elem = obj.find("polygon")
                if poly_elem is not None:
                    # Check for our format
                    if poly_elem.findall("point"):
                        print(f"[TRAINING] Detected polygon annotations (our format) in dataset")
                        return True
                    
                    # Check for Roboflow format
                    x1_elem = poly_elem.find("x1")
                    if x1_elem is not None:
                        print(f"[TRAINING] Detected polygon annotations (Roboflow format) in dataset")
                        return True
        except Exception as e:
            print(f"[WARN] Error reading {xml_file}: {e}")
            continue
    
    print(f"[TRAINING] No polygon annotations found - dataset has only bboxes")
    return False
