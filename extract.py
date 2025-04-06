import argparse
import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import dateparser
import spacy
import json

nlp = spacy.load("en_core_web_sm")

def extract_fields(text):
    data = {}
    other = {}

    # Regex: Client/Patient Name
    name_match = re.search(r"(Patient Name|Client Name|Name):\s*(.+)", text, re.IGNORECASE)
    if name_match:
        data["Matter.Client.Name"] = name_match.group(2).strip()

    # Date of Loss
    dol_match = re.search(r"(Date of (Incident|Loss)):\s*([\d/.-]+)", text, re.IGNORECASE)
    if dol_match:
        parsed_date = dateparser.parse(dol_match.group(3))
        if parsed_date:
            data["Matter.Custom.DateOfLoss"] = str(parsed_date.date())

    # Phone Number
    phone_match = re.search(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", text)
    if phone_match:
        data["Contact.Client.Phone"] = phone_match.group(1)

    # Hours Worked (paystub-style)
    hours_match = re.search(r"Total Hours Worked.*?([\d]+\.\d+)", text, re.IGNORECASE)
    if hours_match:
        data["Matter.Client.HoursWorked"] = hours_match.group(1)

    # NLP Entities
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            other.setdefault("Matter.Custom.Provider", ent.text)

    return data, other

def save_extracted_data(output_path, file_name, fields, other_fields):
    base = os.path.splitext(os.path.basename(file_name))[0]
    output_file = os.path.join(output_path, f"{base}_extracted.json")

    with open(output_file, 'w') as f:
        json.dump({
            "clio_fields": fields,
            "other_fields": other_fields
        }, f, indent=2)

    print(f"💾 Output saved to: {output_file}")

def process_pdf_smart(pdf_path, output_path):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i + 1}: {pdf_path} ---")

            text = page.extract_text()
            if text and len(text.strip()) > 30:
                print("✅ Text-based PDF detected.")
                fields, other = extract_fields(text)
            else:
                print("📷 Scanned PDF detected – applying OCR...")
                image = convert_from_path(pdf_path, first_page=i + 1, last_page=i + 1)[0]
                text = pytesseract.image_to_string(image)
                fields, other = extract_fields(text)

            print("🧾 Extracted Fields for Clio:")
            if fields:
                for k, v in fields.items():
                    print(f"✅ {k} → {v}")
            else:
                print("⚠️ No Clio-compatible fields were found.")

            if other:
                print("\n📋 Other Fields Detected (Unmapped):")
                for k, v in other.items():
                    print(f"- {k}: {v}")

            save_extracted_data(output_path, pdf_path, fields, other)

def process_image(file_path, output_path):
    text = pytesseract.image_to_string(Image.open(file_path))
    fields, other = extract_fields(text)

    print("🧾 Extracted Fields for Clio:")
    for k, v in fields.items():
        print(f"✅ {k} → {v}")

    if other:
        print("\n📋 Other Fields Detected (Unmapped):")
        for k, v in other.items():
            print(f"- {k}: {v}")

    save_extracted_data(output_path, file_path, fields, other)

def batch_process_folder(folder_path, output_path):
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        if filename.lower().endswith(".pdf"):
            process_pdf_smart(full_path, output_path)
        elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
            process_image(full_path, output_path)

def main():
    parser = argparse.ArgumentParser(description="Extract Clio-ready fields from scanned PDFs or images")
    parser.add_argument("--file", help="Path to a single PDF or image file")
    parser.add_argument("--folder", help="Path to a folder of PDFs/images to batch process")
    parser.add_argument("--output", default="output", help="Directory to save extracted .json files")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.folder:
        batch_process_folder(args.folder, args.output)
    elif args.file:
        if args.file.lower().endswith(".pdf"):
            process_pdf_smart(args.file, args.output)
        else:
            process_image(args.file, args.output)
    else:
        print("⚠️ Please provide either --file or --folder argument.")

if __name__ == "__main__":
    main()
