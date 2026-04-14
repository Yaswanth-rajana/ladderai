import pdfplumber
import re
from typing import Dict, Any, List, Optional

class PDFParser:
    def __init__(self):
        self.text = ""
        self.tables = []
    
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main method to parse PDF and extract text and tables
        """
        result = {
            "success": False,
            "text": "",
            "tables": [],
            "pages": 0,
            "error": None
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result["pages"] = len(pdf.pages)
                full_text = []
                
                # Extract text from each page
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(f"--- Page {page_num} ---\n{page_text}")
                    
                    # Extract tables from each page
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            if table and len(table) > 1:  # At least 2 rows
                                result["tables"].append({
                                    "page": page_num,
                                    "data": table
                                })
                
                result["text"] = "\n\n".join(full_text)
                result["success"] = True
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_clean_text(self, pdf_path: str) -> str:
        """
        Extract and clean text from PDF
        """
        result = self.parse(pdf_path)
        if result["success"]:
            # Basic cleaning
            text = result["text"]
            # Remove extra whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            # Remove empty lines
            text = re.sub(r'^\s*$\n', '', text, flags=re.MULTILINE)
            return text
        return ""
    
    def get_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """
        Extract all tables from PDF
        """
        result = self.parse(pdf_path)
        if result["success"]:
            return [table["data"] for table in result["tables"]]
        return []


# Quick test function
def test_parser():
    import os
    import json
    
    parser = PDFParser()
    
    # Look for your uploaded PDF
    uploads_dir = "./uploads"
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in uploads/ folder")
        print("   Upload a PDF first using POST /documents/upload")
        return
    
    test_pdf = os.path.join(uploads_dir, pdf_files[0])
    print(f"📄 Testing parser on: {test_pdf}\n")
    
    # Parse the PDF
    result = parser.parse(test_pdf)
    
    if result["success"]:
        print(f"✅ Successfully parsed PDF")
        print(f"   Pages: {result['pages']}")
        print(f"   Text length: {len(result['text'])} characters")
        print(f"   Tables found: {len(result['tables'])}")
        
        print("\n" + "="*50)
        print("📝 EXTRACTED TEXT (First 1000 chars):")
        print("="*50)
        print(result["text"][:1000])
        
        if result["tables"]:
            print("\n" + "="*50)
            print("📊 TABLES FOUND:")
            print("="*50)
            for i, table in enumerate(result["tables"][:2]):  # Show first 2 tables
                print(f"\nTable {i+1} (Page {table['page']}):")
                for row in table["data"][:5]:  # Show first 5 rows
                    print(f"  {row}")
    else:
        print(f"❌ Failed to parse: {result['error']}")

if __name__ == "__main__":
    test_parser()