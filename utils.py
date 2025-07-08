# utils.py
import docx
import PyPDF2
from io import BytesIO
import textstat
import language_tool_python
import streamlit as st # Import streamlit for st.cache_resource

# Initialize LanguageTool globally or within a cached function for efficiency
# This downloads the necessary data on first run, so it might take a moment.
@st.cache_resource
def get_language_tool():
    """
    Initializes and returns a LanguageTool instance.
    Uses Streamlit's caching to ensure it's only initialized once.
    """
    return language_tool_python.LanguageTool('en-US') # You can change to 'en-GB', 'en-AU' etc.

def extract_text_from_file(uploaded_file):
    """
    Extracts text content from uploaded files (.txt, .pdf, .docx).

    Args:
        uploaded_file: The file object uploaded via Streamlit's st.file_uploader.

    Returns:
        str: The extracted text content, or an empty string if extraction fails.
    """
    file_type = uploaded_file.type

    if file_type == "text/plain":
        # Decode as UTF-8, handling potential errors
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")
    elif file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(uploaded_file)
    else:
        return ""

def extract_text_from_pdf(uploaded_pdf_file):
    """
    Extracts text from a PDF file.

    Args:
        uploaded_pdf_file: The file object of the PDF.

    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    try:
        # PyPDF2 expects a file-like object, BytesIO wraps the uploaded file content
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_pdf_file.getvalue()))
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() if page.extract_text() else ""
    except Exception as e:
        # print(f"Error reading PDF: {e}") # For debugging, can be removed in production
        text = "" # Return empty string on error
    return text

def extract_text_from_docx(uploaded_docx_file):
    """
    Extracts text from a DOCX file.

    Args:
        uploaded_docx_file: The file object of the DOCX.

    Returns:
        str: Extracted text from the DOCX.
    """
    text = ""
    try:
        # python-docx expects a file-like object, BytesIO wraps the uploaded file content
        document = docx.Document(BytesIO(uploaded_docx_file.getvalue()))
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        # print(f"Error reading DOCX: {e}") # For debugging, can be removed in production
        text = "" # Return empty string on error
    return text

def calculate_readability_scores(text):
    """
    Calculates various readability scores and text statistics for the given text.

    Args:
        text (str): The input text to analyze.

    Returns:
        dict: A dictionary containing various readability scores and text stats.
    """
    if not text.strip(): # Check if text is empty or only whitespace
        return {
            "Word Count": 0,
            "Sentence Count": 0,
            "Character Count": 0,
            "Flesch Reading Ease": "N/A",
            "Flesch-Kincaid Grade Level": "N/A",
            "Gunning Fog Index": "N/A",
            "SMOG Index": "N/A",
            "ARI (Automated Readability Index)": "N/A",
            "Coleman-Liau Index": "N/A",
            "Dale-Chall Readability Score": "N/A",
            "LIX Score": "N/A",
            "RIX Score": "N/A",
            "Text Standard": "N/A"
        }

    scores = {
        "Word Count": textstat.lexicon_count(text),
        "Sentence Count": textstat.sentence_count(text),
        "Character Count": len(text),
        "Flesch Reading Ease": textstat.flesch_reading_ease(text),
        "Flesch-Kincaid Grade Level": textstat.flesch_kincaid_grade(text),
        "Gunning Fog Index": textstat.gunning_fog(text),
        "SMOG Index": textstat.smog_index(text),
        "ARI (Automated Readability Index)": textstat.automated_readability_index(text),
        "Coleman-Liau Index": textstat.coleman_liau_index(text),
        "Dale-Chall Readability Score": textstat.dale_chall_readability_score(text),
        "LIX Score": textstat.lix(text),
        "RIX Score": textstat.rix(text),
        "Text Standard": textstat.text_standard(text, float_output=False)
    }
    return scores


def check_grammar(text):
    """
    Checks the grammar of the given text using LanguageTool.

    Args:
        text (str): The input text to check.

    Returns:
        list: A list of dictionaries, where each dictionary represents a grammar match/error.
    """
    if not text.strip():
        return []

    tool = get_language_tool()
    matches = tool.check(text)

    # Convert matches to a more friendly dictionary format for display
    grammar_errors = []
    for match in matches:
        grammar_errors.append({
            "Context": text[match.offset:match.offset + match.errorLength],
            "Message": match.message,
            "Category": match.ruleId, # More granular category, e.g., MORFOLOGIK_RULE_EN_US
            "Rule Name": match.ruleIssueType, # e.g., Typos, Grammar, Punctuation, Style
            "Suggested Correction": ", ".join(match.replacements) if match.replacements else "N/A",
            "Offset": match.offset, # Added for potential debugging/advanced use
            "Length": match.errorLength # Added for potential debugging/advanced use
        })
    return grammar_errors
