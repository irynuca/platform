import os
import camelot
import pdfplumber
import pandas as pd
from ftfy import fix_text

#### nu am putut folosi acest script, nu se descurca, am recurs in final la conversia pdf to xlsx prin ilovepdf
# -----------------------------------
# 🔧 Path Manager Helper
# -----------------------------------
BASE_DIR = r"C:\Users\irina\Project Element\Data source"

def get_company_paths(ticker: str, pdf_filename: str):
    company_folder = os.path.join(BASE_DIR, ticker)
    raw_pdf_folder = os.path.join(company_folder, f"{ticker}_raw")
    tables_output_folder = os.path.join(raw_pdf_folder, f"{ticker}_raw_tables")
    
    pdf_path = os.path.join(raw_pdf_folder, pdf_filename)
    pdf_base = os.path.splitext(pdf_filename)[0]

    return {
        "pdf_path": pdf_path,
        "tables_output_folder": tables_output_folder,
        "table_filename_template": lambda table_num: f"{pdf_base}_rawtable{table_num}.csv"
    }


def fix_unicode_advanced(text):
    return fix_text(text) if isinstance(text, str) else text

# -----------------------------------
# 🐫 Try extraction with Camelot
# -----------------------------------
def extract_with_camelot(paths):
    print("📥 Trying extraction with Camelot (lattice)...")
    try:
        tables = camelot.read_pdf(paths["pdf_path"], pages="all", flavor="lattice")
        if tables.n == 0:
            print("⚠️ No tables found with lattice. Retrying with stream mode...")
            tables = camelot.read_pdf(paths["pdf_path"], pages="all", flavor="stream", strip_text="\n")

        if tables.n > 0:
            print(f"✅ Camelot extracted {tables.n} tables.")
            os.makedirs(paths["tables_output_folder"], exist_ok=True)

            for i, table in enumerate(tables):
                # Clean the extracted DataFrame
                try:
                    df = table.df.applymap(lambda x: fix_unicode_advanced(x).strip() if isinstance(x, str) else x)
                    output_path = os.path.join(
                        paths["tables_output_folder"],
                        paths["table_filename_template"](i + 1))
                    df.to_csv(output_path, index=False)
                except Exception as e:
                    print(f"⚠️ Skipping table {i + 1} due to error: {e}")
            return tables.n
        else:
            print("❌ Camelot could not extract tables in either mode.")
            return 0
    except Exception as e:
        print(f"❌ Camelot failed: {e}")
        return 0

# -----------------------------------
# 🔍 Fallback with pdfplumber
# -----------------------------------
def extract_with_pdfplumber(paths):
    print("📥 Trying extraction with pdfplumber...")
    count = 0
    try:
        with pdfplumber.open(paths["pdf_path"]) as pdf:
            os.makedirs(paths["tables_output_folder"], exist_ok=True)
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for i, table in enumerate(tables):
                    df = pd.DataFrame(table)
                    output_path = os.path.join(paths["tables_output_folder"], paths["table_filename_template"](f"{page_num}_{i + 1}"))
                    df.to_csv(output_path, index=False)
                    count += 1
        print(f"✅ pdfplumber extracted {count} tables.")
    except Exception as e:
        print(f"❌ pdfplumber failed: {e}")

# -----------------------------------
# 🚀 Main Runner
# -----------------------------------
if __name__ == "__main__":
    ticker = "AQ"
    pdf_filename = "AQ_conso_ro_30.06.2024.pdf"

    paths = get_company_paths(ticker, pdf_filename)
    camelot_tables = extract_with_camelot(paths)

    if camelot_tables == 0:
        extract_with_pdfplumber(paths)
