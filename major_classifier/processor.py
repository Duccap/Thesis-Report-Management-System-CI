import os
import re
import uuid
import timeit
import pdfplumber
from datetime import datetime
import json
from dotenv import load_dotenv
from database import Database
from producer import Producer
from file_manager import get_file_from_bucket, remove_file_from_dir, write_to_bucket, upload_file_to_bucket
from annotation import process_annotation

# Load environment variables
load_dotenv()


def classify_major(uploaded_file_location):
    """
    Classify the major of the thesis based on the text from the first page of the PDF.

    Args:
        uploaded_file_location (str): Path to the PDF file.

    Returns:
        str: The detected major, or "Undetermined" if not found.
    """
    try:
        with pdfplumber.open(uploaded_file_location) as pdf:
            # Extract text from the first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Look for the "SCHOOL OF" followed by the major name pattern
            match = re.search(r"SCHOOL OF\s+([A-Za-z\s\-]+)", text, re.IGNORECASE)
            if match:
                # Extract the major name, strip leading/trailing spaces
                major_name = match.group(1).strip()

                # To prevent capturing unwanted content, split by newlines and take the first part
                major_name = re.split(r'\n', major_name)[0].strip()

                return major_name

    except Exception as e:
        print(f"Error processing PDF: {e}")

    # Return 'Undetermined' if no major is detected or there's an error
    return "Undetermined"

def insert_database(event_id, thesis_id, file_location, major, annotation_file_location=None):
    """
    Insert the result and annotation file location into the database.

    Args:
        event_id (str): The event ID.
        thesis_id (str): The thesis ID.
        file_location (str): The location of the output file.
        major (str): The detected major.
        annotation_file_location (str): The location of the annotation file (optional).
    """
    file_name = os.path.basename(file_location)
    uploaded_time = datetime.utcnow()

    db = Database()
    db.insert(
        "INSERT INTO output (id, thesis_id, file_name, file_location, annotation_file_location, result, uploaded_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (event_id, thesis_id, file_name, file_location, annotation_file_location, major, uploaded_time)
    )

    print("Inserted in database", flush=True)



def output_file(cloud_file_location):
    start_time = timeit.default_timer()

    file_name = os.path.basename(cloud_file_location).split(".")[0]
    service_type = os.environ.get("APP_NAME")
    thesis_id = file_name
    event_id = str(uuid.uuid4())

    producer = Producer()

    uploaded_file_location = get_file_from_bucket(cloud_file_location)
    producer.publish_status(event_id, thesis_id, service_type, "Processing")

    output = ""
    try:
        # Classify major
        major = classify_major(uploaded_file_location)

        # Prepare output text
        output += f"Detected Major: {major}\n"

        # Write output to cloud bucket
        output_file_location = write_to_bucket(file_name, output)
        print(f"\nTime for {os.environ.get('APP_NAME')} to process file {file_name} is {timeit.default_timer() - start_time}\n", flush=True)

        print(f"Finished uploading to bucket for {os.environ.get('APP_NAME')}", flush=True)

        # Generate, upload, and insert annotation
        annotation_file_location = process_annotation(thesis_id, major, uploaded_file_location)

        # Remove local file
        remove_file_from_dir(uploaded_file_location)

        # Insert results into database
        insert_database(event_id, thesis_id, output_file_location, major, annotation_file_location)

        # Publish status
        producer.publish_message(event_id, thesis_id, service_type, output_file_location, major)

        # Publish annotation
        producer.publish_annotation(event_id, thesis_id, service_type, annotation_file_location)

        print(f"Processing complete in {os.environ.get('APP_NAME')}", flush=True)

    except Exception as e:
        print(f"Error during processing: {e}", flush=True)
        producer.publish_status(event_id, thesis_id, service_type, "Service error")