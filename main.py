# main.py
import streamlit as st
import pandas as pd
from utils import extract_text_from_file, calculate_readability_scores, check_grammar

# --- Helper functions for color coding ---
def get_flesch_reading_ease_color(score):
    if not isinstance(score, (int, float)):
        return "gray" # For N/A
    if score >= 60: # Generally considered easy to read
        return "green"
    elif score >= 30: # Fairly difficult to difficult
        return "orange"
    else: # Very difficult
        return "red"

def get_grade_level_color(score):
    if not isinstance(score, (int, float)):
        return "gray" # For N/A
    # Assuming lower grade levels are "better" for general readability
    if score <= 8: # Up to 8th grade is often target for general audience
        return "green"
    elif score <= 12: # High school level
        return "orange"
    else: # College level and above
        return "red"

def get_overall_grade_color(grade_text):
    if "5th" in grade_text or "6th" in grade_text or "7th" in grade_text or "8th" in grade_text:
        return "green"
    elif "9th" in grade_text or "10th" in grade_text or "11th" in grade_text or "12th" in grade_text:
        return "orange"
    elif "College" in grade_text or "Graduate" in grade_text:
        return "red"
    return "gray" # For N/A or other values

def main():
    st.set_page_config(page_title="Document Analyzer", layout="wide", initial_sidebar_state="auto")
    st.title("📝 Document Readability & Grammar Analyzer")
    st.markdown("""
        Upload your document (text, PDF, or Word) or paste text directly below
        to get an instant readability assessment, word count, and grammar check.
    """)

    # --- File Uploader Section ---
    st.subheader("Upload Your Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["txt", "pdf", "docx"],
        help="Upload a .txt, .pdf, or .docx file to analyze its content."
    )

    st.markdown("---") # Separator

    # --- Text Area Input Section ---
    st.subheader("Or Paste Your Text Here")

    # Initialize session state for the text area if not already present
    if 'pasted_text_content' not in st.session_state:
        st.session_state['pasted_text_content'] = ""

    pasted_text = st.text_area(
        "Paste your text here",
        height=250,
        help="Enter the text you want to analyze directly.",
        value=st.session_state['pasted_text_content'], # Connect to session state
        key="pasted_text_input" # Essential for linking to session state
    )

    text_content_to_analyze = "" # This variable will hold the actual text for analysis

    # Determine the source of text: uploaded file takes precedence
    if uploaded_file is not None:
        st.info(f"Analyzing uploaded file: **{uploaded_file.name}**")
        with st.spinner("Extracting text from file..."):
            text_content_to_analyze = extract_text_from_file(uploaded_file)
        # Clear pasted text in session state if a file is uploaded to avoid confusion
        if 'pasted_text_content' in st.session_state:
            st.session_state['pasted_text_content'] = "" # This will visually clear the text area

    elif pasted_text.strip(): # Use pasted text if no file and text area has content
        st.info("Analyzing text from the input box.")
        text_content_to_analyze = pasted_text
        # Update session state with the current pasted text to persist it if the user causes a rerun
        st.session_state['pasted_text_content'] = pasted_text
    else:
        st.info("Please upload a file or paste text to get started.")


    # --- Analysis and Display Section (Only run if text_content_to_analyze is available) ---
    if text_content_to_analyze.strip(): # Check if text_content_to_analyze actually has content after processing
        st.success("Text obtained successfully! Performing analysis...")

        # Extracted Text Preview
        st.subheader("Extracted Text Preview:")
        with st.expander("Click to view processed text"):
            # Limit display to 1000 chars for large texts
            st.code(text_content_to_analyze[:1000] + "..." if len(text_content_to_analyze) > 1000 else text_content_to_analyze)

        # Calculate Readability & Stats
        with st.spinner("Calculating readability scores and text statistics..."):
            scores = calculate_readability_scores(text_content_to_analyze)

        st.subheader("📊 Readability Analysis & Statistics")

        # Display Word Count, Sentence Count, Character Count in columns
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        with stats_col1:
            st.metric(label="Word Count", value=scores['Word Count'])
        with stats_col2:
            st.metric(label="Sentence Count", value=scores['Sentence Count'])
        with stats_col3:
            st.metric(label="Character Count", value=scores['Character Count'])
        st.markdown("---")

        # Display key readability scores with color coding
        col1, col2, col3 = st.columns(3)
        with col1:
            flesch_score = scores['Flesch Reading Ease']
            flesch_color = get_flesch_reading_ease_color(flesch_score)
            st.markdown(f"<h3 style='color:{flesch_color};'>Flesch Reading Ease: {flesch_score:.2f}</h3>", unsafe_allow_html=True)
            st.info("Higher score = Easier to read (Target: 60-70 for general audience)")
        with col2:
            fk_grade = scores['Flesch-Kincaid Grade Level']
            fk_color = get_grade_level_color(fk_grade)
            st.markdown(f"<h3 style='color:{fk_color};'>Flesch-Kincaid Grade: {fk_grade:.2f}</h3>", unsafe_allow_html=True)
            st.info("Lower score = Easier to read (Target: 7-9 for general audience)")
        with col3:
            text_standard = scores['Text Standard']
            ts_color = get_overall_grade_color(text_standard)
            st.markdown(f"<h3 style='color:{ts_color};'>Overall Text Standard: {text_standard}</h3>", unsafe_allow_html=True)
            st.info("Approximate grade level needed to understand the text.")

        st.markdown("---")

        st.subheader("All Readability Scores:")
        scores_for_df = {k: v for k, v in scores.items() if k not in ["Word Count", "Sentence Count", "Character Count"]} # Exclude new counts from this table
        scores_df = pd.DataFrame.from_dict(scores_for_df, orient='index', columns=['Score'])
        scores_df.index.name = 'Metric'
        st.dataframe(scores_df)

        st.markdown("---")

        # Grammar Check Section
        st.subheader("📚 Grammar and Spelling Check")
        with st.spinner("Performing grammar and spelling check..."):
            grammar_errors = check_grammar(text_content_to_analyze)

        if grammar_errors:
            st.error(f"Found {len(grammar_errors)} potential grammar/spelling issues!")
            with st.expander("Click to view detailed grammar issues"):
                grammar_df = pd.DataFrame(grammar_errors)
                st.dataframe(grammar_df)
        else:
            st.success("No significant grammar or spelling issues found! 🎉")

        st.markdown("---")

        st.subheader("💡 Understanding the Scores:")
        st.markdown("""
        Readability scores estimate the difficulty of a text. Here's a quick guide:

        * **Flesch Reading Ease**: Higher scores mean easier to read.
            * <span style='color:green;'>**Green (≥60)**: Easy to read (e.g., 5th-7th grade level).</span>
            * <span style='color:orange;'>**Orange (30-59)**: Fairly difficult to difficult (e.g., 8th-12th grade level).</span>
            * <span style='color:red;'>**Red (<30)**: Very difficult (e.g., college graduate level).</span>
        * **Flesch-Kincaid Grade Level / Gunning Fog / SMOG / ARI / Coleman-Liau**: Estimates the U.S. grade level needed to understand the text. Lower scores mean easier to read.
            * <span style='color:green;'>**Green (≤8)**: Appropriate for general audiences.</span>
            * <span style='color:orange;'>**Orange (9-12)**: High school level, potentially harder for some.</span>
            * <span style='color:red;'>**Red (>12)**: College level or highly academic.</span>
        * **Text Standard**: Provides a general grade level range recommendation. Color-coded similarly to grade levels.

        **Note:** Readability and grammar checks are statistical/rule-based estimates and should be used as a guide, not a definitive measure. They don't account for content complexity, vocabulary uniqueness, or reader's background knowledge. Always review suggested corrections!
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
