import os
import argparse
from collections import defaultdict
from tabulate import tabulate
import csv

def scan_folder(path, export_csv=False):
    folder_count = 0
    file_count = 0
    file_stats = defaultdict(lambda: {"count": 0, "size": 0})

    for root, dirs, files in os.walk(path):
        folder_count += len(dirs)
        file_count += len(files)
        for file in files:
            ext = os.path.splitext(file)[1].lower() or "no_ext"
            full_path = os.path.join(root, file)
            try:
                size = os.path.getsize(full_path)
            except:
                size = 0
            file_stats[ext]["count"] += 1
            file_stats[ext]["size"] += size

    table = [
        (ext, data["count"], sizeof_fmt(data["size"]))
        for ext, data in sorted(file_stats.items())
    ]

    print("\n📁 File Types Summary:")
    print(tabulate(table, headers=["Extension", "Count", "Total Size"], tablefmt="grid"))

    print(f"\n📂 Total folders: {folder_count}")
    print(f"📄 Total files: {file_count}")

    if export_csv:
        csv_path = os.path.join(path, "folder_summary.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Extension", "Count", "Total Size (bytes)"])
            for ext, data in sorted(file_stats.items()):
                writer.writerow([ext, data["count"], data["size"]])
        print(f"\n📤 Summary exported to: {csv_path}")

def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} P{suffix}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count folders, files, and file types in a directory.")
    parser.add_argument("path", help="Path to the folder to scan")
    parser.add_argument("--csv", action="store_true", help="Export summary as CSV")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print("❌ Error: Path does not exist.")
    elif not os.path.isdir(args.path):
        print("❌ Error: Path is not a folder.")
    else:
        scan_folder(args.path, export_csv=args.csv)
