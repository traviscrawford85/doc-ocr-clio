# run_pipeline.py

import os
import argparse
from utils import ocr  # your reusable module
from folder_inventory.scan_folder import scan_folder  # if modularized

# TODO: import other pipeline modules as you build them
# from summarize_document import summarize
# from document_type_detector import detect_types
# from classify_document import classify_documents
# from extract_schema import extract_fields
# from rename_document import rename_files

def run_pipeline(folder, steps, output_dir=None):
    print(f"\n📂 Starting pipeline for: {folder}\n")

    if "inventory" in steps:
        print("🔍 Inventory...")
        scan_folder(folder)  # or pass export_csv=True if needed

    if "ocr" in steps:
        print("🧠 OCR Preprocessing...")
        ocr_cache = os.path.join(folder, "ocr_cache")
        for file in os.listdir(folder):
            if file.lower().endswith(".pdf"):
                path = os.path.join(folder, file)
                result = ocr.ocr_pdf_if_needed(path, output_dir=ocr_cache)
                print(f"{file}: {result['status']}")

    if "summarize" in steps:
        print("📝 Summarizing...")
        # summarize(folder, ...)

    if "classify" in steps:
        print("📂 Classifying...")
        # classify_documents(folder, ...)

    if "extract" in steps:
        print("🧾 Extracting schema fields...")
        # extract_fields(folder, ...)

    if "rename" in steps:
        print("🪪 Renaming files...")
        # rename_files(folder, ...)

    if "report" in steps:
        print("📊 Generating report...")
        # generate_report(folder, output_format='xlsx' if args.xlsx else 'csv')

    print("\n✅ Pipeline complete.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full legal document processing pipeline.")
    parser.add_argument("folder", help="Target folder of documents")
    parser.add_argument("--ocr", action="store_true", help="Run OCR if needed")
    parser.add_argument("--summarize", action="store_true", help="Summarize documents")
    parser.add_argument("--classify", action="store_true", help="Classify document types")
    parser.add_argument("--extract", action="store_true", help="Extract schema fields")
    parser.add_argument("--rename", action="store_true", help="Rename files")
    parser.add_argument("--report", action="store_true", help="Export inventory or classification report")
    parser.add_argument("--xlsx", action="store_true", help="Export report as Excel")
    parser.add_argument("--inventory", action="store_true", help="Show folder/file breakdown")
    args = parser.parse_args()

    steps = []
    for flag in ["inventory", "ocr", "summarize", "classify", "extract", "rename", "report"]:
        if getattr(args, flag):
            steps.append(flag)

    if not steps:
        print("❌ No steps specified. Use --ocr, --summarize, etc.")
    else:
        run_pipeline(args.folder, steps, output_dir=os.path.join(args.folder, "output"))
