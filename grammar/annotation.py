import fitz
import os
import json
import uuid
import logging
from datetime import datetime
from file_manager import upload_file_to_bucket, remove_file_from_dir

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def generate_grammar_annotation(thesis_id, enhanced_matches, text_blocks, pdf_file_path):
    annotations = []
    
    try:
        logger.info(f"Opening PDF for annotation: {pdf_file_path}")
        doc = fitz.open(pdf_file_path)
        
        for match_idx, match in enumerate(enhanced_matches):
            try:
                page = doc[match["page"]]
                page_height = page.rect.height
                
                x0 = match["x0"]
                y0 = page_height - match["bottom"]
                x1 = match["x1"]
                y1 = page_height - match["top"]
                
                annotation = {
                    "@context": [
                        "https://www.w3.org/ns/anno.jsonld",
                        "https://comments.acrobat.com/ns/anno.jsonld"
                    ],
                    "source": "service",
                    "type": "Annotation",
                    "id": str(uuid.uuid4()),
                    "bodyValue": (
                        f"Grammar Issue: {match['message']}\n"
                        f"Found: '{match['matched_text']}'\n"
                        f"Suggestions: {', '.join(match['replacements'])}"
                    ),
                    "motivation": "commenting",
                    "target": {
                        "source": thesis_id,
                        "selector": {
                            "type": "AdobeAnnoSelector",
                            "node": {"index": match["page"]},
                            "subtype": "highlight",
                            "boundingBox": [x0, y0, x1, y1],
                            "quadPoints": [
                                x0, y1,
                                x1, y1,
                                x0, y0,
                                x1, y0
                            ],
                            "strokeColor": "#FF0000",
                            "strokeWidth": 1.5,
                            "opacity": 0.4
                        }
                    },
                    "creator": {
                        "type": "Person",
                        "name": os.environ.get("APP_NAME", "grammar-service")
                    },
                    "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "modified": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                annotations.append(annotation)
                
                logger.debug(f"Created annotation for match {match_idx} on page {match['page']+1}")
                
            except Exception as e:
                logger.error(f"Error creating annotation for match {match_idx}: {str(e)}")

        logger.info(f"Generated {len(annotations)} precise annotations")
        return annotations

    except Exception as e:
        logger.error(f"Error in annotation generation: {str(e)}", exc_info=True)
        return []

def process_grammar_annotation(thesis_id, enhanced_matches, text_blocks, pdf_file_path):
    annotation_file_location = None

    try:
        if not enhanced_matches:
            logger.info("No grammar issues found - skipping annotation generation")
            return None

        logger.info(f"Starting annotation processing for {thesis_id}")
        logger.info(f"Processing {len(enhanced_matches)} grammar issues")

        annotations = generate_grammar_annotation(
            thesis_id,
            enhanced_matches,
            text_blocks,
            pdf_file_path
        )
        
        if not annotations:
            logger.warning("No annotations were generated")
            return None

        logger.info(f"Successfully generated {len(annotations)} annotations")
        
        os.makedirs("temp", exist_ok=True)
        annotation_file_name = f"{thesis_id}_grammar_annotation.json"
        annotation_file_path = os.path.join("temp", annotation_file_name)
        
        with open(annotation_file_path, "w") as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved annotations to {annotation_file_path}")

        annotation_file_location = upload_file_to_bucket(annotation_file_path)
        logger.info(f"Uploaded annotations to {annotation_file_location}")

        remove_file_from_dir(annotation_file_path)
        logger.debug("Removed local annotation file")

        return annotation_file_location

    except Exception as e:
        logger.error(f"Error in process_grammar_annotation: {str(e)}", exc_info=True)
        return None
