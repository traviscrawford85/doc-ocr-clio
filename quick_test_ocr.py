import argparse
import pytesseract
import pdfplumber
from PIL import Image
import spacy
import re
import dateparser
from pdf2image import convert_from_path
import os

nlp = spacy.load("en_core_web_sm")

def extract_fields(text):
    data = {}

    # Extract Patient Name
    name_match = re.search(r"(Patient Name|Name):\s*(.+)", text, re.IGNORECASE)
    if name_match:
        data["Matter.Client.Name"] = name_match.group(2).strip()

    # Extract Date of Loss
    dol_match = re.search(r"(Date of (Incident|Loss)):\s*([\d/.-]+)", text, re.IGNORECASE)
    if dol_match:
        parsed_date = dateparser.parse(dol_match.group(3))
        if parsed_date:
            data["Matter.Custom.DateOfLoss"] = str(parsed_date.date())

    # NLP: Named Entities
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            data.setdefault("Matter.Custom.Provider", ent.text)

    return data

def process_image(file_path):
    print(f"\n📷 Processing image: {file_path}")
    text = pytesseract.image_to_string(Image.open(file_path))
    fields = extract_fields(text)
    for key, value in fields.items():
        print(f"✅ {key}: {value}")

def process_pdf(pdf_path):
    print(f"\n📄 Processing PDF: {pdf_path}")
    images = convert_from_path(pdf_path)
    for i, image in enumerate(images):
        print(f"\n--- Page {i+1} ---")
        temp_img_path = f"temp_page_{i+1}.png"
        image.save(temp_img_path)
        process_image(temp_img_path)
        os.remove(temp_img_path)

def main():
    parser = argparse.ArgumentParser(description="Quick test OCR + NLP field extraction")
    parser.add_argument("--file", required=True, help="Path to image or PDF file")
    args = parser.parse_args()

    if args.file.lower().endswith(".pdf"):
        process_pdf(args.file)
    else:
        process_image(args.file)

if __name__ == "__main__":
    main()