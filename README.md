# Price Mapping Engine – Federal Procurement Data

## 📊 Overview
This project builds an end-to-end data pipeline to process unstructured federal procurement PDFs and transform them into an analysis-ready dataset.

The system extracts:
- Vendor name
- Contract value
- Service category
- Contract date

and generates a **price mapping engine** for vendor-level analysis.

---

## 🎯 Problem Statement
Federal procurement data is published as unstructured PDFs, making it difficult to extract and analyze vendor pricing information.

This project addresses:
- Unstructured data ingestion
- Data extraction and transformation
- Vendor-level price intelligence

---

## 🏗️ Architecture (Medallion Model)

### 🟤 Bronze Layer
- OCR-based ingestion (PDF → text)
- Multi-document batch processing

### ⚪ Silver Layer
- Regex-based structured extraction
- Data cleaning and normalization
- Vendor name standardization

### 🟡 Gold Layer
- Vendor-level price mapping
- Time-based trend analysis
- High-value contract detection
- Price type classification (unit vs total)

---

## ⚙️ Tech Stack
- Python (pandas, pytesseract, pdf2image)
- SQLite
- Regex

---

## 📊 Key Outputs

### 🔹 Price Mapping
- Raytheon Co. → $1.61B
- Ferrovial Construccion PR LLC → $1.08B
- General Dynamics Land Systems → $716M

### 🔹 Price Type Distribution
- Total Contract Value → 7
- Price per Unit → 2

### 🔹 Insights
- Identifies top-performing vendors
- Tracks contract value trends over time
- Enables competitive pricing analysis

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
- high_value_flag
- price_type

---
## 🤖 AI-Native Extraction (Updated)

The extraction layer has been redesigned from a rule-based (regex) approach to an AI-native, layout-agnostic system.

Instead of relying on fixed patterns, the system interprets context to extract:
- Vendor of record  
- Payment amount  
- Service/product  
- Action Forms relevance  
- Proxy vendor relationships  

This enables the pipeline to handle highly unstructured documents across thousands of varying layouts without manual rule updates.

## 🔍 Proxy Vendor Detection

In real-world datasets, payments are often routed through intermediaries (billing partners), while the actual product differs from the vendor of record.

This system identifies such cases by inferring functional equivalence from context.

Example:
- Vendor: Global Tech Solutions  
- Description: Digital workflow / form processing  
- Inference: Equivalent to Action Forms  

This allows the engine to detect “money through the noise” even when the product is not explicitly mentioned.

## 🧠 LLM Design Approach

The extraction logic is designed to be model-agnostic and can integrate with:
- OpenAI GPT  
- Google Gemini  
- Local LLMs  

The current implementation demonstrates LLM behavior using a simulated layer, focusing on reasoning and generalization rather than hardcoded rules.

## 🚀 How to Run

```bash
pip install -r requirements.txt
python src/pipeline.py
