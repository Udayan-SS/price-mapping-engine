# Price Mapping Engine – Federal Procurement Data

## 📊 Overview
This project implements an end-to-end data pipeline to process unstructured federal procurement PDFs and transform them into an analysis-ready dataset.

The system extracts:
- Vendor name
- Contract value
- Service category
- Contract date

and generates a **price mapping engine** to analyze vendor performance across contracts.

---

## 🎯 Problem Statement
Federal procurement data is often published as unstructured PDF documents, making it difficult to extract and analyze vendor pricing and contract information.

This project addresses:
- Unstructured data ingestion
- Data extraction and transformation
- Vendor-level price analysis

---

## 🏗️ Architecture (Medallion Model)

### 🟤 Bronze Layer (Raw Ingestion)
- Ingested multiple DoD contract PDFs
- Converted PDF → text using OCR (Tesseract)

### ⚪ Silver Layer (Transformation)
- Extracted structured data using regex
- Cleaned OCR noise and normalized vendor names
- Removed duplicates

### 🟡 Gold Layer (Analytics)
- Vendor-level price mapping
- Contract trend analysis over time
- Analysis-ready dataset

---

## ⚙️ Tech Stack
- Python (pandas, pytesseract, pdf2image)
- SQLite (data storage)
- Regex (pattern extraction)

---

## 📊 Key Outputs

### 🔹 Price Mapping
- Raytheon Co. → $1.61B
- Ferrovial Construccion PR LLC → $1.08B
- General Dynamics Land Systems → $716M

### 🔹 Insights
- Identifies top-performing vendors
- Tracks contract values across time
- Enables competitive analysis

---

## 🧱 Data Model

### Vendors Table
- vendor_id
- vendor_name

### Agencies Table
- agency_id
- agency_name

### Contracts Table
- vendor_id
- agency_id
- service_category
- contract_value
- contract_date

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python src/pipeline.py
