# utils.py
import docx
import PyPDF2
from io import BytesIO
import textstat
import language_tool_python
import streamlit as st # For st.cache_resource
import torch # For transformers backend
from transformers import pipeline

# --- Cached Resources for external models/tools ---

@st.cache_resource
def get_language_tool():
    """
    Initializes and returns a LanguageTool instance.
    Uses Streamlit's caching to ensure it's only initialized once per session.
    """
    # 'en-US' is default, can be changed to 'en-GB', 'en-AU' etc.
    return language_tool_python.LanguageTool('en-US')

@st.cache_resource
def get_sentiment_pipeline():
    """
    Initializes and returns a sentiment analysis pipeline from transformers.
    Uses Streamlit's caching to ensure the model is loaded only once per session.
    """
    # Model for general English sentiment analysis (positive, negative, neutral)
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@st.cache_resource
def get_style_pipeline():
    """
    Initializes and returns a text style (formal/informal) classification pipeline.
    Uses Streamlit's caching to ensure the model is loaded only once per session.
    """
    # Model for classifying text formality (Formal, Informal)
    return pipeline("text-classification", model="LenDigLearn/formality-classifier-mdeberta-v3-base")


# --- Text Extraction Functions ---

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
        # print(f"Error reading PDF: {e}") # Uncomment for debugging if needed
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
        # print(f"Error reading DOCX: {e}") # Uncomment for debugging if needed
        text = "" # Return empty string on error
    return text

# --- Readability and Text Statistics Functions ---

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
        "Character Count": len(text), # Includes spaces and punctuation
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

# --- Grammar Checking Function ---

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

    grammar_errors = []
    for match in matches:
        grammar_errors.append({
            "Context": text[match.offset:match.offset + match.errorLength],
            "Message": match.message,
            "Category": match.ruleId,
            "Rule Name": match.ruleIssueType,
            "Suggested Correction": ", ".join(match.replacements) if match.replacements else "N/A",
            "Offset": match.offset,
            "Length": match.errorLength
        })
    return grammar_errors

# --- Tone Analysis Function ---

def analyze_tone(text):
    """
    Analyzes the sentiment/tone of the given text.

    Args:
        text (str): The input text to analyze.

    Returns:
        dict: A dictionary containing the sentiment label (POSITIVE, NEGATIVE, NEUTRAL)
              and its confidence score, or N/A if text is empty.
    """
    if not text.strip():
        return {"label": "N/A", "score": "N/A"}

    # Transformers models have a token limit (e.g., 512). Truncate for efficiency.
    # The sentiment will be based on this truncated portion.
    max_length = 500
    truncated_text = text[:max_length]

    nlp_pipeline = get_sentiment_pipeline()
    try:
        # The pipeline returns a list of dicts, e.g., [{'label': 'POSITIVE', 'score': 0.999}]
        result = nlp_pipeline(truncated_text)[0]
        return result
    except Exception as e:
        # print(f"Error during sentiment analysis: {e}") # Uncomment for debugging
        return {"label": "Error", "score": "N/A"}

# --- Style Classification Function ---

def analyze_style(text):
    """
    Analyzes the text style (Formal/Informal).

    Args:
        text (str): The input text to analyze.

    Returns:
        dict: A dictionary containing the style label (Formal, Informal)
              and its confidence score, or N/A if text is empty.
    """
    if not text.strip():
        return {"label": "N/A", "score": "N/A"}

    # Style models also have token limits, truncate similar to sentiment
    max_length = 500
    truncated_text = text[:max_length]

    style_pipeline = get_style_pipeline()
    try:
        # The pipeline returns a list of dicts, e.g., [{'label': 'Formal', 'score': 0.98}]
        result = style_pipeline(truncated_text)[0]
        return result
    except Exception as e:
        # print(f"Error during style analysis: {e}") # Uncomment for debugging
        return {"label": "Error", "score": "N/A"}
