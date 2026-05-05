# =========================================================
# STEP 1: BRONZE LAYER - PDF TO RAW TEXT USING OCR
# =========================================================

# Import required libraries
from pdf2image import convert_from_path   # Converts PDF → images
import pytesseract                        # OCR engine (image → text)
import os                                 # File handling

# Set path to Tesseract executable (IMPORTANT for Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set path to Poppler (required by pdf2image)
poppler_path = r"C:\poppler\Library\bin"

# Folder containing raw PDFs
pdf_folder = "data/raw_pdfs/"

# Variable to store all extracted text
all_text = ""

# Loop through each PDF file in folder
for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):
        print(f"Processing file: {file}")
        
        # Convert PDF pages to images
        images = convert_from_path(
            os.path.join(pdf_folder, file),
            poppler_path=poppler_path
        )

        # Perform OCR on each page
        for page_number, img in enumerate(images):
            text = pytesseract.image_to_string(img, config='--psm 6')
            all_text += text + "\n"

# Preview first part of extracted text (for validation)
print("\n===== SAMPLE EXTRACTED TEXT =====\n")
print(all_text[:1500])

# =========================================================
# STEP 2: FIXED PARSING LOGIC (STRICT PATTERN)
# =========================================================

import re
import pandas as pd

# Clean text first (important for OCR noise)
clean_text = re.sub(r"\n+", " ", all_text)   # remove line breaks
clean_text = re.sub(r"\s+", " ", clean_text)  # normalize spaces

# Improved regex:
# - Start with capitalized company name
# - Must be followed by location + "was awarded"
pattern = r"([A-Z][A-Za-z0-9&\.\-\s]+?),\s+[A-Za-z\s,]+?,\s+was awarded a\s+\$([\d,]+).*?contract for\s+(.*?)(?:\.)"

matches = re.findall(pattern, clean_text)

data = []

for m in matches:
    vendor = m[0].strip()
    value = int(m[1].replace(",", ""))
    category = m[2].strip()

    data.append({
        "vendor": vendor,
        "contract_value": value,
        "service_category": category,
        "agency": "Department of Defense"
    })

df = pd.DataFrame(data)
df["vendor"] = df["vendor"].str.replace(r"^(ARMY|NAVY|AIR FORCE)\s+", "", regex=True)

print("\n===== FIXED STRUCTURED DATA =====\n")
print(df.head(10))

# =========================================================
# STEP 3: GOLD LAYER - ANALYTICS & INSIGHTS
# =========================================================

# Flag high-value contracts (> $100,000)
df["high_value_flag"] = df["contract_value"] > 100000

# Aggregate total contract value per vendor
vendor_summary = df.groupby("vendor")["contract_value"].sum().reset_index()

# Sort vendors by highest total contract value
vendor_summary = vendor_summary.sort_values(by="contract_value", ascending=False)

print("\n===== TOP VENDORS BY CONTRACT VALUE =====\n")
print(vendor_summary.head())

# =========================================================
# STEP 4: SCD TYPE 2 (TRACK HISTORICAL CHANGES)
# =========================================================

# Add columns to track historical changes
df["start_date"] = "2026-04-30"  # Ideally extract from file name
df["end_date"] = None
df["is_current"] = True

# =========================================================
# STEP 5: SAVE FINAL DATASET
# =========================================================

output_path = "output/final_contracts.csv"

df.to_csv(output_path, index=False)

print(f"\nData successfully saved to: {output_path}")

