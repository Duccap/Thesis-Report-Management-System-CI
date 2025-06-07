import os
import uuid
import timeit
import pdfplumber
import language_tool_python
import logging
from datetime import datetime
from database import Database
from producer import Producer
from file_manager import get_file_from_bucket, remove_file_from_dir, write_to_bucket
from annotation import process_grammar_annotation
import re

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_grammar(uploaded_file_location):
    try:
        logger.info("Initializing LanguageTool with adjusted settings")
        tool = language_tool_python.LanguageTool('en-US', config={
            'cacheSize': 1000,
            'pipelineCaching': True
        })
        
        logger.info(f"Extracting text with positions from {uploaded_file_location}")
        text_blocks = []
        full_text = ""
        
        with pdfplumber.open(uploaded_file_location) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words(
                    x_tolerance=2,
                    y_tolerance=2,
                    keep_blank_chars=False,
                    use_text_flow=True,
                    extra_attrs=["fontname", "size"]
                )
                
                page_text = ""
                for word in words:
                    text_blocks.append({
                        "text": word["text"],
                        "x0": word["x0"],
                        "x1": word["x1"],
                        "top": word["top"],
                        "bottom": word["bottom"],
                        "page": page_num,
                        "font": word["fontname"],
                        "size": word["size"]
                    })
                    page_text += word["text"] + " "
                
                full_text += page_text

        full_text = full_text.strip()
        if not full_text:
            logger.warning("No text extracted from PDF")
            return [], "", []

        logger.info(f"Checking grammar on {len(full_text)} characters")
        matches = tool.check(full_text)
        
        enhanced_matches = []
        technical_terms = {
            "whiskerz", "greendale", "api", "sql", "json", "xml", "html", "css", "javascript",
            "python", "java", "github", "mysql", "postgresql", "mongodb", "redux", "nodejs",
            "reactjs", "angularjs", "vuejs", "tensorflow", "pytorch", "kubernetes", "docker",
            "aws", "gcp", "azure", "firebase", "oauth", "jwt", "crud", "rest", "graphql",
            "microservices", "devops", "cicd", "webpack", "npm", "yarn", "scss", "sass",
            "typescript", "php", "laravel", "django", "flask", "springboot", "elasticsearch","nextjs",
            "nuxtjs", "vuex", "redux-saga", "rxjs", "jest", "mocha", "chai", "cypress","argocd"
        }
        
        academic_terms = {
            "thesis", "dissertation", "bibliography", "appendix", "acknowledgments",
            "supervisor", "co-supervisor", "faculty", "department", "university",
            "semester", "academic", "research", "methodology", "analysis", "conclusion"
        }
        
        skip_rules = {
            "WHITESPACE_RULE", "COMMA_PARENTHESIS_WHITESPACE", "DOUBLE_PUNCTUATION",
            "ENGLISH_WORD_REPEAT_BEGINNING_RULE", "SENTENCE_WHITESPACE",
            "UPPERCASE_SENTENCE_START", "PUNCTUATION_PARAGRAPH_END"
        }
        
        important_categories = {
            "GRAMMAR", "TYPOS", "CONFUSED_WORDS", "PUNCTUATION", "STYLE",
            "REDUNDANCY", "SEMANTICS", "LOGIC", "COHERENCE"
        }
        
        for match in matches:
            matched_text = full_text[match.offset:match.offset + match.errorLength].strip()
            
            if match.ruleId in skip_rules:
                logger.debug(f"Skipping rule {match.ruleId}: {matched_text}")
                continue
            
            if is_likely_proper_name(matched_text):
                logger.debug(f"Skipping probable proper name: {matched_text}")
                continue
            
            if matched_text.lower() in technical_terms:
                logger.debug(f"Skipping technical term: {matched_text}")
                continue
                
            if matched_text.lower() in academic_terms:
                logger.debug(f"Skipping academic term: {matched_text}")
                continue
            
            if is_minor_spelling_issue(match, matched_text, important_categories):
                logger.debug(f"Skipping minor spelling variation: {matched_text}")
                continue
            
            if is_citation_or_reference(matched_text, match.context):
                logger.debug(f"Skipping citation/reference: {matched_text}")
                continue
            
            if is_acronym_or_abbreviation(matched_text):
                logger.debug(f"Skipping acronym/abbreviation: {matched_text}")
                continue

            match_text = full_text[match.offset:match.offset+match.errorLength]
            matching_blocks = []
            current_pos = 0
            for block in text_blocks:
                block_end = current_pos + len(block["text"])
                if (current_pos <= match.offset < block_end) or \
                   (match.offset <= current_pos < match.offset+match.errorLength):
                    matching_blocks.append(block)
                current_pos = block_end + 1

            if matching_blocks:
                first_block = matching_blocks[0]
                last_block = matching_blocks[-1]
                
                enhanced_match = {
                    "message": match.message,
                    "context": match.context,
                    "replacements": match.replacements,
                    "category": match.category,
                    "page": first_block["page"],
                    "x0": first_block["x0"],
                    "x1": last_block["x1"],
                    "top": min(b["top"] for b in matching_blocks),
                    "bottom": max(b["bottom"] for b in matching_blocks),
                    "matched_text": match_text
                }
                enhanced_matches.append(enhanced_match)
            else:
                logger.debug(f"No position found for match: {match.context}")

        logger.info(f"Found {len(enhanced_matches)} enhanced grammar issues")
        return enhanced_matches, full_text, text_blocks

    except Exception as e:
        logger.error(f"Error in adjusted check_grammar: {str(e)}", exc_info=True)
        return [], "", []

def insert_database(event_id, thesis_id, file_location, result, grade, annotation_file_location=None):
    try:
        file_name = os.path.basename(file_location)
        uploaded_time = datetime.utcnow()

        db = Database()
        db.insert(
            """INSERT INTO output 
            (id, thesis_id, file_name, file_location, annotation_file_location, result, grade, uploaded_time) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (event_id, thesis_id, file_name, file_location, annotation_file_location, result, str(grade), uploaded_time)
        )

        logger.info(f"Inserted results into database for {thesis_id}")

    except Exception as e:
        logger.error(f"Database insertion failed: {str(e)}", exc_info=True)

def output_file(cloud_file_location):
    start_time = timeit.default_timer()
    file_name = os.path.basename(cloud_file_location).split(".")[0]
    thesis_id = file_name
    event_id = str(uuid.uuid4())
    producer = Producer()

    try:
        logger.info(f"Starting processing for thesis: {thesis_id}")
        logger.debug(f"Event ID: {event_id}")

        logger.info(f"Downloading file from {cloud_file_location}")
        uploaded_file_location = get_file_from_bucket(cloud_file_location)
        producer.publish_status(event_id, thesis_id, "grammar", "Processing")

        logger.info("Starting grammar analysis")
        matches, full_text, text_blocks = check_grammar(uploaded_file_location)
        
        total_words = len(full_text.split()) if full_text else 0
        words_with_issues = sum(len(m['context'].split()) for m in matches) if matches else 0
        grade = round((total_words - words_with_issues) / total_words * 100) if total_words else 100
        result = "Pass" if grade > 50 else "Fail"
        
        logger.info(
            f"Analysis complete - Grade: {grade}%, "
            f"Words: {total_words}, "
            f"Issues: {words_with_issues}"
        )

        output_content = []
        if matches:
            output_content.append("GRAMMAR ISSUES FOUND:\n")
            for i, match in enumerate(matches[:100]):
                output_content.append(
                    f"Issue {i+1} [Page {match['page']+1}]:\n"
                    f"Type: {match['category']}\n"
                    f"Message: {match['message']}\n"
                    f"Text: '{match['matched_text']}'\n"
                    f"Context: {match['context']}\n"
                    f"Suggestions: {', '.join(match['replacements'])}\n"
                )
            if len(matches) > 100:
                output_content.append(f"\n...and {len(matches)-100} more issues not shown\n")
        else:
            output_content.append("No grammar issues found\n")
        
        output_content.append(
            f"\nSUMMARY:\n"
            f"Total words: {total_words}\n"
            f"Words with issues: {words_with_issues}\n"
            f"Score: {grade}%\n"
            f"Result: {result}\n"
        )
        
        output = '\n'.join(output_content)

        logger.info("Saving results to cloud storage")
        output_file_location = write_to_bucket(file_name, output)
        
        logger.info("Generating PDF annotations")
        annotation_file_location = None
        if matches:
            annotation_file_location = process_grammar_annotation(
                thesis_id, 
                matches, 
                text_blocks, 
                uploaded_file_location
            )

        logger.debug("Cleaning up temporary files")
        remove_file_from_dir(uploaded_file_location)

        logger.info("Storing results in database")
        insert_database(
            event_id, 
            thesis_id, 
            output_file_location, 
            result, 
            grade, 
            annotation_file_location
        )

        logger.info("Publishing results")
        producer.publish_message(
            event_id, 
            thesis_id, 
            "grammar", 
            output_file_location, 
            result, 
            str(grade)
        )
        
        if annotation_file_location:
            producer.publish_annotation(
                event_id, 
                thesis_id, 
                "grammar", 
                annotation_file_location
            )

        processing_time = timeit.default_timer() - start_time
        logger.info(
            f"Processing completed successfully in {processing_time:.2f} seconds\n"
            f"Results: {output_file_location}\n"
            f"Annotations: {annotation_file_location or 'None'}"
        )
        
        print(
            f"\nTime for grammar to process file {file_name}: {processing_time:.2f}s\n"
            f"Final grade: {grade}% ({result})\n", 
            flush=True
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        producer.publish_status(event_id, thesis_id, "grammar", "Service error")
        print(f"Error during processing: {e}", flush=True)
        raise

def is_likely_proper_name(text):
    if len(text) <= 2 or len(text) > 50:
        return False
    
    if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', text):
        return True
    
    if text.isupper() and text.isalpha() and 2 < len(text) < 10:
        return True
    
    if re.match(r'^[A-Z][a-z]*[A-Z][a-z]*', text):
        return True
    
    return False


def is_minor_spelling_issue(match, matched_text, important_categories):
    if match.category in important_categories:
        return False
    
    if match.ruleId.startswith("MORFOLOGIK_RULE"):
        if any(rep.lower() in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'] 
               for rep in match.replacements):
            return False
        return True
    
    return False


def is_citation_or_reference(text, context):
    citation_patterns = [
        r'\b\d{4}\b',
        r'\bp\.\s*\d+',
        r'\bvol\.\s*\d+',
        r'\bno\.\s*\d+',
        r'\bet\s+al\.',
        r'\bibid\.',
        r'\bop\.\s*cit\.',
        r'\[\d+\]',
    ]
    
    for pattern in citation_patterns:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    
    if '(' in context and ')' in context:
        return True
    
    return False


def is_acronym_or_abbreviation(text):
    if text.isupper() and text.isalpha() and 2 <= len(text) <= 8:
        return True
    
    if '.' in text and len(text) <= 10:
        return True
    
    common_abbrevs = {
        'etc', 'vs', 'ie', 'eg', 'cf', 'ca', 'et', 'al', 'op', 'cit',
        'ibid', 'loc', 'vol', 'ed', 'eds', 'trans', 'rev', 'repr',
        'fig', 'figs', 'table', 'ch', 'sec', 'app', 'ref', 'refs'
    }
    
    if text.lower() in common_abbrevs:
        return True
    
    return False
