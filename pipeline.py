# =========================================================
# PROJECT: Price Mapping Engine for Federal Procurement Data
# AUTHOR: Udayan S S
# DESCRIPTION:
# This pipeline ingests unstructured PDF documents (DoD contracts),
# extracts vendor, pricing, and service data using OCR + regex,
# and transforms it into an analysis-ready dataset and SQL schema.
# =========================================================


# ========================
# STEP 0: IMPORT LIBRARIES
# ========================
from pdf2image import convert_from_path   # Convert PDF to images
import pytesseract                        # OCR (image → text)
import os
import re
import pandas as pd
import sqlite3


# ========================
# STEP 1: CONFIGURATION
# ========================

# Path to Tesseract OCR executable (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Path to Poppler (required for pdf2image)
poppler_path = r"C:\poppler\Library\bin"

# Input folder containing PDF files
pdf_folder = "data/raw_pdfs/"


# ========================
# STEP 2: BRONZE LAYER
# ========================
# Convert PDFs → raw text using OCR

documents = []  # store (filename, extracted_text)

for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):
        print(f"Processing: {file}")

        images = convert_from_path(
            os.path.join(pdf_folder, file),
            poppler_path=poppler_path
        )

        text = ""

        for img in images:
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(img, config='--psm 6')
            text += extracted_text + "\n"

        documents.append((file, text))


# ========================
# STEP 3: HELPER FUNCTION
# ========================
# Extract date from filename (used for time analysis)

def extract_date_from_filename(filename):
    match = re.search(r'_(apr|may)(\d{1,2})_(\d{4})', filename, re.IGNORECASE)

    if match:
        month = match.group(1).lower()
        day = int(match.group(2))
        year = int(match.group(3))

        month_map = {
            "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
            "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
        }

        return pd.to_datetime(f"{year}-{month_map[month]:02d}-{day:02d}")

    return None


# ========================
# STEP 4: SILVER LAYER
# ========================
# Clean text and extract structured data

rows = []

# Regex pattern to extract:
# Vendor → Contract Value → Service Description
pattern = r"([A-Z][A-Za-z0-9&\.\-\s]+?),\s+[A-Za-z\s,]+?,\s+was awarded a\s+\$([\d,]+).*?contract for\s+(.*?)(?:\.)"

for filename, raw_text in documents:

    # Clean OCR noise (remove line breaks, normalize spacing)
    clean_text = re.sub(r"\n+", " ", raw_text)
    clean_text = re.sub(r"\s+", " ", clean_text)

    matches = re.findall(pattern, clean_text, re.IGNORECASE | re.DOTALL)

    for m in matches:
        vendor = m[0].strip()
        value = int(m[1].replace(",", ""))
        category = m[2].strip()

        rows.append({
            "vendor": vendor,
            "contract_value": value,
            "service_category": category,
            "agency": "Department of Defense",
            "contract_date": extract_date_from_filename(filename),
            "source_file": filename
        })


# Convert to DataFrame
df = pd.DataFrame(rows)


# ========================
# STEP 5: DATA CLEANING
# ========================

# Remove incorrect vendor captures (OCR noise)
df = df[~df["vendor"].str.contains("contracting activity", case=False)]

# Remove military section prefixes like "ARMY"
df["vendor"] = df["vendor"].str.replace(
    r"^(ARMY|NAVY|AIR FORCE)\s+", "", regex=True
)
# Normalize vendor names for consistent grouping
df["vendor"] = df["vendor"].replace({
    "Raytheon RTX": "Raytheon Co."
})

# Remove duplicates
df = df.drop_duplicates(
    subset=["vendor", "contract_value", "service_category", "contract_date"]
)

# ========================
# 🔥 REQUIREMENT 1: HIGH VALUE FLAG
# ========================
df["high_value_flag"] = df["contract_value"] > 100000


# ========================
# 🔥 REQUIREMENT 2: PRICE TYPE CLASSIFICATION
# ========================
def classify_price_type(text):
    text = text.lower()

    if "per unit" in text or "each" in text or "unit price" in text:
        return "Price per Unit"
    else:
        return "Total Contract Value"

df["price_type"] = df["service_category"].apply(classify_price_type)


# ========================
# PREVIEW
# ========================
print("\n===== CLEANED DATA SAMPLE =====\n")
print(df.head())

# ========================
# STEP 6: GOLD LAYER
# ========================
# Generate insights (Price Mapping Engine)

# Vendor → Agency price mapping
price_map = df.groupby(["vendor", "agency"])["contract_value"].sum().reset_index()

price_map = price_map.sort_values(by="contract_value", ascending=False)

print("\n===== PRICE MAP =====\n")
print(price_map.head(10))


# Vendor trend over time
vendor_trend = df.groupby(["vendor", "contract_date"])["contract_value"].sum().reset_index()

print("\n===== VENDOR TREND =====\n")
print(vendor_trend.head(10))

print("\n===== PRICE TYPE DISTRIBUTION =====\n")
print(df["price_type"].value_counts())


# ========================
# STEP 7: SAVE OUTPUT
# ========================

# Save CSV output
df.to_csv("output/final_contracts.csv", index=False)


# ========================
# STEP 8: SQL STORAGE
# ========================
# Store structured data into SQLite database
import sqlite3

conn = sqlite3.connect("output/contracts.db")

# -------- Vendors Table --------
vendors = df[["vendor"]].drop_duplicates().reset_index(drop=True)
vendors["vendor_id"] = vendors.index + 1

# -------- Agencies Table --------
agencies = df[["agency"]].drop_duplicates().reset_index(drop=True)
agencies["agency_id"] = agencies.index + 1

# -------- Contracts Table --------
contracts = df.merge(vendors, on="vendor", how="left") \
              .merge(agencies, on="agency", how="left")

contracts = contracts[[
    "vendor_id",
    "agency_id",
    "service_category",
    "contract_value",
    "contract_date",
    "source_file",
    "high_value_flag"
]]

# Save all tables
vendors.to_sql("vendors", conn, if_exists="replace", index=False)
agencies.to_sql("agencies", conn, if_exists="replace", index=False)
contracts.to_sql("contracts", conn, if_exists="replace", index=False)

conn.commit()

print("\nSQL Tables Created Successfully")

# -------- Example Query (Price Mapping) --------
query = """
SELECT v.vendor, a.agency, SUM(c.contract_value) AS total_value
FROM contracts c
JOIN vendors v ON c.vendor_id = v.vendor_id
JOIN agencies a ON c.agency_id = a.agency_id
GROUP BY v.vendor, a.agency
ORDER BY total_value DESC
"""

result = pd.read_sql_query(query, conn)

print("\n===== SQL PRICE MAP =====\n")
print(result)

conn.close()