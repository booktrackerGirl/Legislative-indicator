import os
import csv
import gc
import re
import time
import logging
from typing import List

import pandas as pd
import pdfplumber
import spacy
from tqdm import tqdm

from langdetect import detect
from deep_translator import GoogleTranslator

import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from io import BytesIO


# ============================================================
# CONFIG
# ============================================================

PDF_FOLDER = "./data/pdfs"   # Folder where doc_id.pdf files exist

HEALTH_TERMS_FILE = "./keywords/health_terms.txt"
ADAPTATION_TERMS_FILE = "./keywords/adaptation_terms.txt"
HEALTH_AUTHORITY_FILE = "./keywords/health_authority_terms.txt"

INPUT_DATA = "./data/extended_failed_extractions.csv"
OUTPUT_FILE = "./annotation/health_annotation_final_1.csv"
LOG_FILE = "./annotation/pipeline_log_1.txt"

WINDOW_SIZE = 100
MIN_OVERLAP_WORDS = 20
CHUNK_SIZE = 5000

OUTPUT_COLUMNS = [
    "Doc ID",
    "Country",
    "Year",
    "Response",
    "Health relevance (1/0)",
    "Health adaptation mandate (1/0)",
    "Institutional health role (1/0)",
    "Extracted health text",
    "Notes"
]


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# NLP
# ============================================================

nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
nlp.add_pipe("sentencizer")


# ============================================================
# KEYWORD LOADING
# ============================================================

def load_keyword_set(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


# ============================================================
# LEGAL OBLIGATION REGEX
# ============================================================

OBLIGATION_REGEX = re.compile(
    r"\b("
    r"shall|must|is required to|are required to|shall ensure|must ensure|shall establish|"
    r"shall implement|shall develop|shall provide|shall adopt|shall include|obliged to|"
    r"mandatory|mandated|compulsory|duty to|responsible for ensuring|binding|"
    r"statutory requirement|legal obligation|enforceable"
    r")\b",
    re.IGNORECASE
)

NEGATION_REGEX = re.compile(
    r"\b(shall not|must not|not required to|no obligation to)\b",
    re.IGNORECASE
)


# ============================================================
# PDF EXTRACTOR
# ============================================================

class LocalPDFExtractor:
    """
    Extracts text from local PDFs.
    Automatically switches to OCR if the PDF is scanned.
    """

    def __init__(self, pdf_folder: str):
        self.pdf_folder = pdf_folder

    def extract_content(self, doc_id):
        pdf_path = os.path.join(self.pdf_folder, f"{doc_id}.pdf")

        if not os.path.exists(pdf_path):
            logging.warning(f"PDF not found for {doc_id}")
            return None

        try:
            # --- Step 1: direct extraction ---
            text_pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text_pages.append(page.extract_text() or "")

            text = "\n".join(text_pages).strip()

            # --- Step 2: detect scanned PDF ---
            if len(text) < 200:
                logging.info(f"OCR triggered for {doc_id}")
                text = self._ocr_pdf(pdf_path)

            if len(text) < 200:
                return None

            return {
                "text": text,
                "metadata": {
                    "source": "local_pdf",
                    "doc_id": doc_id
                }
            }

        except Exception as e:
            logging.warning(f"Extraction error for {doc_id}: {e}")
            return None


    def _ocr_pdf(self, pdf_path):
        """
        Perform OCR on a PDF using PyMuPDF (fitz) and pytesseract.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: OCR-extracted text from the PDF.
        """
        try:
            ocr_text = []

            # Open PDF with fitz
            doc = fitz.open(pdf_path)

            for page in doc:
                # Render page to image (PNG format)
                pix = page.get_pixmap(dpi=200)
                img = Image.open(BytesIO(pix.tobytes("png")))

                # OCR
                text = pytesseract.image_to_string(img)
                ocr_text.append(text)

            return "\n".join(ocr_text)

        except Exception as e:
            logging.warning(f"OCR failed for {pdf_path}: {e}")
            return ""



# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def contains_any(text: str, keywords: List[str]) -> bool:
    text = text.lower()
    return any(k in text for k in keywords)


def has_obligation(text: str) -> bool:
    if NEGATION_REGEX.search(text):
        return False
    return bool(OBLIGATION_REGEX.search(text))


# ============================================================
# TRANSLATION
# ============================================================

def detect_and_translate(text: str, chunk_size: int = 4000) -> str:
    try:
        lang = detect(text[:1000])
        if lang == "en":
            return text

        translator = GoogleTranslator(source=lang, target="en")
        translated_chunks = []

        start = 0
        while start < len(text):
            chunk = text[start:start + chunk_size]
            translated_chunks.append(translator.translate(chunk))
            start += chunk_size

        return " ".join(translated_chunks)

    except Exception as e:
        logging.warning(f"Translation failed: {e}")
        return text


# ============================================================
# WINDOW EXTRACTION
# ============================================================

def extract_relevant_windows(text: str, health_terms: List[str],
                             window_size: int = WINDOW_SIZE,
                             min_overlap: int = MIN_OVERLAP_WORDS) -> str:

    text = re.sub(r"\s+", " ", text)
    words = text.split()
    n = len(words)

    positions = []
    for i, w in enumerate(words):
        for k in health_terms:
            if k in w.lower():
                positions.append(i)

    if not positions:
        return ""

    windows = [(max(0, p - window_size), min(n, p + window_size)) for p in positions]
    windows.sort()
    merged = [windows[0]]

    for start, end in windows[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end - min_overlap:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return "\n\n".join(" ".join(words[s:e]) for s, e in merged)


# ============================================================
# CSV WRITER
# ============================================================

def append_row(row: dict, filepath: str):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ============================================================
# PROCESS DOCUMENT
# ============================================================

def process_document(row, extractor, health_terms, adaptation_terms, health_authority_terms):
    doc_id = str(row["Document ID"])
    country = row["Geographies"]
    year = row["Publication Year"]
    response = row["Topic/Response"]

    result = extractor.extract_content(doc_id)

    if not result or not result.get("text", "").strip():
        return {
            "Doc ID": doc_id,
            "Country": country,
            "Year": year,
            "Response": response,
            "Health relevance (1/0)": 0,
            "Health adaptation mandate (1/0)": 0,
            "Institutional health role (1/0)": 0,
            "Extracted health text": "",
            "Notes": "Extraction failed"
        }

    text = detect_and_translate(result["text"])
    words = text.split()

    extracted_chunks = []
    health_relevance = 0
    health_mandate = 0
    institutional_role = 0

    for i in range(0, len(words), CHUNK_SIZE):
        chunk_text = " ".join(words[i:i + CHUNK_SIZE])
        doc = nlp(chunk_text)
        sentences = [s.text for s in doc.sents]

        if any(contains_any(s, health_terms) for s in sentences):
            health_relevance = 1
            chunk_extract = extract_relevant_windows(chunk_text, health_terms)
            if chunk_extract:
                extracted_chunks.append(chunk_extract)

        if contains_any(chunk_text, health_authority_terms):
            institutional_role = 1

        for s in sentences:
            if contains_any(s, health_terms) and (
                contains_any(s, adaptation_terms) or has_obligation(s)
            ):
                health_mandate = 1
                break

    extracted_text = "\n\n".join(extracted_chunks)

    return {
        "Doc ID": doc_id,
        "Country": country,
        "Year": year,
        "Response": response,
        "Health relevance (1/0)": health_relevance,
        "Health adaptation mandate (1/0)": health_mandate,
        "Institutional health role (1/0)": institutional_role,
        "Extracted health text": extracted_text,
        "Notes": ""
    }


# ============================================================
# MAIN
# ============================================================

def main():
    logging.info("PIPELINE STARTED")

    health_terms = load_keyword_set(HEALTH_TERMS_FILE)
    adaptation_terms = load_keyword_set(ADAPTATION_TERMS_FILE)
    health_authority_terms = load_keyword_set(HEALTH_AUTHORITY_FILE)

    extractor = LocalPDFExtractor(PDF_FOLDER)

    df = pd.read_csv(INPUT_DATA)
    df = df.rename(columns={"first_event_year": "Publication Year"})
    df = df[[
        "Document ID",
        "Geographies",
        "Topic/Response",
        "Publication Year"
    ]]

    processed_ids = set()
    if os.path.exists(OUTPUT_FILE):
        existing = pd.read_csv(OUTPUT_FILE)
        processed_ids = set(existing["Doc ID"].astype(str))

    for _, row in tqdm(df.iterrows(), total=len(df)):
        doc_id = str(row["Document ID"])

        if doc_id in processed_ids:
            continue

        output_row = process_document(
            row,
            extractor,
            health_terms,
            adaptation_terms,
            health_authority_terms
        )

        append_row(output_row, OUTPUT_FILE)
        gc.collect()

    logging.info("PIPELINE FINISHED")
    print("✔ Processing complete")


if __name__ == "__main__":
    main()
