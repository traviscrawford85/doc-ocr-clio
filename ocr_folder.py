import os
import argparse
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

def ocr_pdf_if_needed(pdf_path, output_dir):
    with pdfplumber.open(pdf_path) as pdf:
        if any(page.extract_text() for page in pdf.pages):
            return "🟢 Skipped (already searchable)"
    
    images = convert_from_path(pdf_path)
    ocr_text = '\n\n'.join(pytesseract.image_to_string(img) for img in images)

    base = os.path.basename(pdf_path).replace('.pdf', '.txt')
    txt_path = os.path.join(output_dir, base)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(ocr_text)
    
    return "🔵 OCR applied"

def process_folder(folder, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    log = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.pdf'):
            path = os.path.join(folder, filename)
            result = ocr_pdf_if_needed(path, output_dir)
            log.append((filename, result))
    return log

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR all non-searchable PDFs in a folder.")
    parser.add_argument("input_folder", help="Folder with PDF files")
    parser.add_argument("output_folder", help="Folder to write OCR'd .txt files")
    args = parser.parse_args()

    summary = process_folder(args.input_folder, args.output_folder)
    for file, status in summary:
        print(f"{file}: {status}")
