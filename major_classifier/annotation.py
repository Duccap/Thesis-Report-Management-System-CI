import fitz
import os
import json
import uuid
from datetime import datetime
from file_manager import upload_file_to_bucket, remove_file_from_dir

def generate_annotation(thesis_id, major, pdf_file_path):
    """
    Generate annotation data for Adobe PDF Embed API using PyMuPDF (Fitz).

    Args:
        thesis_id (str): The ID of the thesis.
        major (str): The detected major.
        pdf_file_path (str): Path to the PDF file.

    Returns:
        dict: Annotation data in JSON format.
    """
    annotation = None

    try:
        # Open the PDF
        doc = fitz.open(pdf_file_path)
        first_page = doc[0]

        # Search for the major text
        matches = first_page.search_for(major)

        if matches:
            rect = matches[0]  # Use the first found occurrence
            x0, y0, x1, y1 = convert_coordinates(first_page, rect)  # Convert to Adobe's coordinate system
            annotaion_id = str(uuid.uuid4())
            annotation = {
                "@context": [
                    "https://www.w3.org/ns/anno.jsonld",
                    "https://comments.acrobat.com/ns/anno.jsonld"
                ],
                "source": "service",
                "type": "Annotation",
                "id": annotaion_id,
                "bodyValue": f"Detected Major: {major}",
                "motivation": "commenting",
                "target": {
                    "source": thesis_id,
                    "selector": {
                        "type": "AdobeAnnoSelector",
                        "node": {
                            "index": 0  # Page number
                        },
                        "subtype": "highlight",
                        "boundingBox": [x0, y0, x1, y1],  
                        "quadPoints": [
                            x0, y1, x1, y1, x0, y0, x1, y0 
                        ],
                        "strokeColor": "#FF0000",
                        "strokeWidth": 2,
                        "opacity": 0.5
                    }
                },
                "creator": {
                    "type": "Person",
                    "name": os.environ.get("APP_NAME")
                },
                "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "modified": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }

    except Exception as e:
        print(f"Error generating annotation: {e}", flush=True)

    return annotation

def convert_coordinates(page, rect):
    """
    Converts PyMuPDF coordinates to Adobe PDF Viewer coordinates.
    
    Args:
        page (fitz.Page): The PDF page object.
        rect (fitz.Rect): The detected bounding box.

    Returns:
        tuple: Converted (x0, y0, x1, y1) coordinates.
    """
    # Get page height
    page_height = page.rect.height  

    # Convert coordinates from PyMuPDF (bottom-left origin) to Adobe (top-left origin)
    x0, y1 = rect.x0, page_height - rect.y0
    x1, y0 = rect.x1, page_height - rect.y1

    return x0, y0, x1, y1

def process_annotation(thesis_id, major, pdf_file_path):
    annotation_file_location = None

    try:
        # Generate annotation
        annotation = generate_annotation(thesis_id, major, pdf_file_path)

        if annotation:
            # Write annotation to a JSON file
            annotation_file_name = f"{thesis_id}_annotation.json"
            annotation_file_path = os.path.join("temp", annotation_file_name)
            os.makedirs(os.path.dirname(annotation_file_path), exist_ok=True)
            with open(annotation_file_path, "w") as f:
                json.dump(annotation, f)

            # Upload annotation file to the bucket
            annotation_file_location = upload_file_to_bucket(annotation_file_path)
            print(f"Annotation file uploaded to {annotation_file_location}", flush=True)

            # Remove local annotation file
            remove_file_from_dir(annotation_file_path)



    except Exception as e:
        print(f"Error processing annotation: {e}", flush=True)

    return annotation_file_location
