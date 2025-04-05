import argparse
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import dateparser
import spacy
import yaml
import json
import os
import itertools

# Load spaCy NLP model once
nlp = spacy.load("en_core_web_sm")

def load_field_config(yaml_path="field_config.yml"):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)["fields"]

def extract_fields(text, field_config):
    data = {}
    fallback = {}
    earnings = {}

    # Deduplicate lines
    lines = list(dict.fromkeys(line.strip() for line in text.splitlines() if line.strip()))

    # Clio-specific mapping
    for clio_field, label_variants in field_config.items():
        for label in label_variants:
            pattern = rf"{label}\s*[:\-]?\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[clio_field] = match.group(1).strip()
                break

    # Fallback label:value matches
    generic_matches = re.findall(r"([A-Z][A-Za-z0-9 .\-]{2,40})\s*[:\-]\s*(.+)", text)
    for label, value in generic_matches:
        fallback[label.strip()] = value.strip()

    # Fallback label on one line, value on next
    for a, b in itertools.pairwise(lines):
        if re.match(r"^[A-Z][A-Za-z0-9 .\-]{2,40}[:\-]?$", a) and b.strip():
            if a.strip().rstrip(":") not in fallback:
                fallback[a.strip().rstrip(":")] = b.strip()

    # Parse financial lines
    for line in lines:
        if re.match(r"^(Federal Income|Medicare|Social Security|Maryland State Income)", line):
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 3:
                label = parts[0].strip()
                this_period = parts[1].strip()
                ytd = parts[2].strip()
                earnings[label] = {"This Period": this_period, "YTD": ytd}

    return data, fallback, earnings

def save_output(fields, fallback, earnings, source_file):
    base_name = os.path.splitext(os.path.basename(source_file))[0]
    output_file = f"output/{base_name}_extracted.json"

    os.makedirs("output", exist_ok=True)

    full_data = {
        "clio_fields": fields,
        "unmapped_fields": fallback,
        "financial_data": earnings
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2)

    print(f"\n💾 Output saved to: {output_file}")

def process_pdf_smart(pdf_path, field_config):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i + 1} ---")

            text = page.extract_text()
            if text and len(text.strip()) > 30:
                print("✅ Text-based PDF detected.")
            else:
                print("📷 Scanned PDF detected – applying OCR...")
                image = convert_from_path(pdf_path, first_page=i + 1, last_page=i + 1)[0]
                text = pytesseract.image_to_string(image)

            fields, fallback, earnings = extract_fields(text, field_config)

            if fields:
                print("🧾 Extracted Fields for Clio:\n")
                for k, v in fields.items():
                    print(f"✅ {k} → {v}")
            else:
                print("⚠️ No Clio-compatible fields were found.")

            if fallback:
                print("\n📋 Other Fields Detected (Unmapped):")
                for k, v in fallback.items():
                    print(f"- {k}: {v}")

            if earnings:
                print("\n💰 Financial Summary:")
                for label, amounts in earnings.items():
                    print(f"- {label}: This Period = {amounts['This Period']} | YTD = {amounts['YTD']}")

            save_output(fields, fallback, earnings, pdf_path)

def process_image(file_path, field_config):
    text = pytesseract.image_to_string(Image.open(file_path))
    fields, fallback, earnings = extract_fields(text, field_config)

    if fields:
        print("🧾 Extracted Fields for Clio:\n")
        for k, v in fields.items():
            print(f"✅ {k} → {v}")
    else:
        print("⚠️ No Clio-compatible fields were found.")

    if fallback:
        print("\n📋 Other Fields Detected (Unmapped):")
        for k, v in fallback.items():
            print(f"- {k}: {v}")

    if earnings:
        print("\n💰 Financial Summary:")
        for label, amounts in earnings.items():
            print(f"- {label}: This Period = {amounts['This Period']} | YTD = {amounts['YTD']}")

    save_output(fields, fallback, earnings, file_path)

def main():
    parser = argparse.ArgumentParser(description="Extract Clio-ready fields and financial data from PDFs/images")
    parser.add_argument("--file", required=True, help="Path to PDF or image file")
    parser.add_argument("--config", default="field_config.yml", help="Path to YAML field config file")
    args = parser.parse_args()

    field_config = load_field_config(args.config)

    if args.file.lower().endswith(".pdf"):
        process_pdf_smart(args.file, field_config)
    else:
        process_image(args.file, field_config)

if __name__ == "__main__":
    main()
