
import re
import os
import uuid
import timeit
import pdfplumber

from datetime import datetime
from dotenv import load_dotenv
from database import Database
from producer import Producer

from sumy.utils import get_stop_words
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer as Summarizer

from file_manager import get_file_from_bucket, remove_file_from_dir, write_to_bucket, get_text_from_bucket

import nltk
import os

# Optional: use a custom path if running in Docker or non-standard env
nltk_data_path = "/usr/local/nltk_data"
os.makedirs(nltk_data_path, exist_ok=True)

nltk.download("punkt", download_dir=nltk_data_path)
nltk.download("punkt_tab", download_dir=nltk_data_path)
nltk.data.path.append(nltk_data_path)
load_dotenv()

def extract_text(uploaded_file_location):
    text = ""

    with pdfplumber.open(uploaded_file_location) as pdf:
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]

            page_text = page.extract_text()
            text += page_text + "\n"

    return text


def extract_chapter_titles(uploaded_file_location):
    chapter_titles = []
    chapter_regex = re.compile("(?:(C(?:hapter|HAPTER)) (\d)+(\.)?[ \n]*([A-Z][a-z/A-Z&/\- ]*)|(R(?:eferences|EFERENCES))|(A(?:bstract|BSTRACT))|(A(?:ppendix|PPENDIX)))( )*(\n)+")
    
    with pdfplumber.open(uploaded_file_location) as pdf:
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            text = page.extract_text()

            chapter_title = re.search(chapter_regex, text)

            if chapter_title:
                chapter_title = chapter_title.group()
                chapter_titles.append(chapter_title)

    return chapter_titles


def extract_section_titles(uploaded_file_location):
    section_titles = []

    with pdfplumber.open(uploaded_file_location) as pdf:
        section_regex = re.compile("(?m)^(\d\.)(\d)?( )*[a-zA-Z0-9 ]+[a-zA-Z0-9\.]{,2}[a-zA-Z0-9 /:-]*( )*(\n)+")
        starting_index = 0
        
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            text = page.extract_text()

            if i == 0:
                if (text[-1].isdigit()) and (int(text[-1]) == 1):
                    starting_index = 1

            section = re.finditer(section_regex, text)

            if section:
                for title in section:
                    title = title.group()

                    section_titles.append(title)

    return section_titles    


def extract_chapter_content(text, chapter_titles, section_titles):
    chapter_content = []
    section_content = []

    for i in range(len(chapter_titles)):
        if i != (len(chapter_titles) - 1):
            if (chapter_titles[i] in text) and (chapter_titles[i + 1] in text):
                start_index = text.index(chapter_titles[i]) + len(chapter_titles[i])
                end_index = text.index(chapter_titles[i + 1])

                content = ""

                for j in range(start_index, end_index):
                    content += text[j]
                
                chapter_content.append([chapter_titles[i], content])
            
    for chapter in chapter_content:
        content = chapter[1]
        updated_chapter_content = []

        for i in range(len(section_titles)):
            if (section_titles[i] in content):
                start_index = content.index(section_titles[i]) + len(section_titles[i])
                section_content = ""

                if (i != len(section_titles) - 1) and (section_titles[i + 1] in content):
                    end_index = content.index(section_titles[i + 1])

                    for j in range(start_index, end_index):
                        section_content += content[j]
                else: 
                    end_index = len(content)

                    for j in range(start_index, end_index):
                        section_content += content[j]

                section = [section_titles[i], section_content]
                updated_chapter_content.append(section)
                    
        if len(updated_chapter_content) > 0:
            chapter[1] = updated_chapter_content      

    return chapter_content


def summarize_text(text):
    stemmer = Stemmer("english")
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = Summarizer(stemmer)
    summarizer.stop_words = get_stop_words("english")
    summary = ""

    for sentence in summarizer(parser.document, 10):
        summary += " " + str(sentence)

    print("done summary", flush=True)
    return summary


def get_summaries(chapter_content):
    output = ""

    for index, chapter in enumerate(chapter_content):
        chapter_title = " ".join(chapter[0].splitlines()).strip("\t\n ")

        if (chapter_title != "REFERENCES") and (chapter_title != "APPENDIX"):
            if index != 0:
                output += "\n"
            output += chapter_title

            if type(chapter[1]) == list:
                for section in chapter[1]:
                    output += "\n\n" + section[0].strip("\n") + ":\n"

                    summary = summarize_text(section[1])
                    output += summary
            else:
                output += "\n\n"
                summary = summarize_text(chapter[1])
                output += summary
        
            output += "\n"

    return output 


def insert_database(event_id, thesis_id, file_location, result):
    file_name = os.path.basename(file_location)
    uploaded_time = datetime.utcnow()

    db = Database()
    db.insert("INSERT INTO output (id, thesis_id, file_name, file_location, result, uploaded_time) VALUES (%s, %s, %s, %s, %s, %s)", (event_id, thesis_id, file_name, file_location, result, uploaded_time))

    print("inserted in db", flush=True)


def output_file(cloud_file_location):
    start_time = timeit.default_timer()

    event_id = str(uuid.uuid4())
    file_name = os.path.basename(cloud_file_location).split(".")[0]
    service_type = os.environ.get("APP_NAME")
    thesis_id = file_name

    producer = Producer()

    print(f"[DEBUG] Downloading file from bucket: {cloud_file_location}", flush=True)
    uploaded_file_location = get_file_from_bucket(cloud_file_location)
    print(f"[DEBUG] Local file path: {uploaded_file_location}", flush=True)
    producer.publish_status(event_id, thesis_id, service_type, "Processing")
    
    try:
        print("[DEBUG] Extracting chapter titles...", flush=True)
        chapter_titles = extract_chapter_titles(uploaded_file_location)
        print(f"[DEBUG] Found chapter titles: {chapter_titles}", flush=True)

        print("[DEBUG] Extracting section titles...", flush=True)
        section_titles = extract_section_titles(uploaded_file_location)
        print(f"[DEBUG] Found section titles: {section_titles}", flush=True)

        print("[DEBUG] Extracting text from PDF...", flush=True)
        text = extract_text(uploaded_file_location)
        print(f"[DEBUG] Extracted text length: {len(text)}", flush=True)

        print("[DEBUG] Extracting chapter content...", flush=True)
        chapter_content = extract_chapter_content(text, chapter_titles, section_titles)
        print(f"[DEBUG] Extracted chapter content count: {len(chapter_content)}", flush=True)

        print("[DEBUG] Generating summaries...", flush=True)
        output = get_summaries(chapter_content)
        print(f"[DEBUG] Output summary length: {len(output)}", flush=True)
        
        result = "None"

        print("[DEBUG] Writing output to bucket...", flush=True)
        output_file_location = write_to_bucket(file_name, output)
        print(f"[DEBUG] Output file location: {output_file_location}", flush=True)

        print("\nTime for " + os.environ.get("APP_NAME") + " to process file " + file_name + " is " + str(timeit.default_timer() - start_time) + "\n", flush=True)

        print("finished uploading to bucket for " + os.environ.get("APP_NAME"), flush=True)

        print("[DEBUG] Removing local file...", flush=True)
        remove_file_from_dir(uploaded_file_location)
        
        print("[DEBUG] Inserting result into database...", flush=True)
        insert_database(event_id, thesis_id, output_file_location, result)

        print("[DEBUG] Publishing message to producer...", flush=True)
        producer.publish_message(event_id, thesis_id, service_type, output_file_location, result)

        print("Processing complete in " + os.environ.get("APP_NAME"), flush=True)
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}", flush=True)
        producer.publish_status(event_id, thesis_id, service_type, "Service error")