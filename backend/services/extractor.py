import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class InvoiceExtractor:
    def __init__(self):
        # Field extraction patterns with synonyms - IMPROVED
        self.patterns = {
            "invoice_number": [
                r"(?:invoice|inv|bill)\s+no[.:]\s*([A-Z0-9][A-Z0-9\-/]+)",  # MOVED TO TOP: "Invoice No: INV-2024-001"
                r"(?:invoice|inv|bill)(?:\s*(?:no|#|number|id))?\s*:?\s*([A-Z0-9][A-Z0-9\-/]+)",
                r"(?:inv\s*#\s*)([A-Z0-9\-/]+)",
                r"invoice\s*number\s*:?\s*([A-Z0-9\-/]+)",
                r"bill\s*id\s*:?\s*([A-Z0-9\-/]+)",
            ],
            "vendor_name": [
                r"(?:vendor|supplier|seller|billed\s*by|from)\s*:?\s*([A-Za-z0-9\s&,.]+)(?:\n|$)",
                r"vendor\s*name\s*:?\s*([A-Za-z0-9\s&,.]+)",
            ],
            "invoice_date": [
                r"(?:date|invoice\s*date|dated)\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
                r"(?:date|invoice\s*date|dated)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            ],
            "total_amount": [
                r"(?:total|amount\s*due|grand\s*total|invoice\s*total)\s*:?\s*[\$£€]?\s*([\d,]+\.?\d*)",
                r"total\s*:?\s*[\$£€]\s*([\d,]+\.?\d*)",
                r"total\s*amount\s*:?\s*[\$£€]?\s*([\d,]+\.?\d*)",
            ],
            "tax_amount": [
                r"(?:tax|vat|gst|tax\s*amount)\s*:?\s*[\$£€]?\s*([\d,]+\.?\d*)",
                r"tax\s*:?\s*[\$£€]\s*([\d,]+\.?\d*)",
            ]
        }
        
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from invoice text
        """
        result = {
            "vendor_name": None,
            "invoice_number": None,
            "invoice_date": None,
            "currency": None,
            "total_amount": None,
            "tax_amount": None,
            "line_items": []
        }
        
        # Extract each field
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1)
                    
                    # Clean and format based on field type
                    if field in ["total_amount", "tax_amount"]:
                        value = self._clean_number(value)
                    elif field == "invoice_date":
                        value = self._normalize_date(value)
                    elif field in ["vendor_name", "invoice_number"]:
                        value = value.strip()
                    
                    result[field] = value
                    break  # Stop after first match
        
        # Special handling: if invoice_number still None, try more aggressive pattern
        if result["invoice_number"] is None:
            # Look for any pattern like INV-XXX or similar
            inv_match = re.search(r'([A-Z]{3,4}[-/][0-9]{3,})', text)
            if inv_match:
                result["invoice_number"] = inv_match.group(1)
        
        # Special handling: if total_amount still None, try to extract from line items sum
        if result["total_amount"] is None:
            line_items = self._extract_line_items(text)
            if line_items:
                total = sum(item.get("line_total", 0) for item in line_items)
                if total > 0:
                    result["total_amount"] = total
        
        # Detect currency
        result["currency"] = self._detect_currency(text)
        
        # Extract line items
        result["line_items"] = self._extract_line_items(text)
        
        return result
    
    def _clean_number(self, value: str) -> Optional[float]:
        """Convert currency string to float"""
        try:
            # Remove commas and currency symbols
            cleaned = re.sub(r'[^\d\.\-]', '', value)
            return float(cleaned)
        except:
            return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Convert various date formats to YYYY-MM-DD"""
        try:
            # Try different formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except:
                    continue
            
            # Try with 2-digit year
            for fmt in ["%d-%m-%y", "%d/%m/%y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except:
                    continue
            
            return date_str
        except:
            return date_str
    
    def _detect_currency(self, text: str) -> str:
        """Detect currency from symbols or codes"""
        if '$' in text or "USD" in text:
            return "USD"
        elif '€' in text or "EUR" in text:
            return "EUR"
        elif '£' in text or "GBP" in text:
            return "GBP"
        elif '₹' in text or "INR" in text:
            return "INR"
        else:
            return "USD"  # Default
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from text
        Handles formats like:
        1. Laptop - 1 x $1000 = $1000
        2. Mouse - 2 x $25 = $50
        """
        line_items = []
        
        # Pattern for numbered line items with description, quantity, price, total
        pattern = r'(\d+)\.\s*([A-Za-z0-9\s]+?)\s*[-]\s*(\d+)\s*x\s*[\$£€]?\s*([\d,]+\.?\d*)\s*=\s*[\$£€]?\s*([\d,]+\.?\d*)'
        
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                item = {
                    "description": match[1].strip(),
                    "quantity": float(match[2]),
                    "unit_price": self._clean_number(match[3]),
                    "line_total": self._clean_number(match[4])
                }
                line_items.append(item)
            except:
                continue
        
        # If no items found with pattern, try simpler pattern
        if not line_items:
            simple_pattern = r'(\d+)\.\s*([^0-9]+?)\s*(\d+)\s*x\s*([\d,]+\.?\d*)'
            matches = re.findall(simple_pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    quantity = float(match[2])
                    unit_price = self._clean_number(match[3])
                    item = {
                        "description": match[1].strip(),
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": quantity * unit_price if unit_price else None
                    }
                    line_items.append(item)
                except:
                    continue
        
        return line_items


# Test function
if __name__ == "__main__":
    extractor = InvoiceExtractor()
    
    # Test with sample text
    test_text = """INVOICE
Invoice No: INV-2024-001
Date: 2024-03-15
Vendor: Acme Corp
Total Amount: $1,250.00
Tax: $100.00
Line Items:
1. Laptop - 1 x $1000 = $1000
2. Mouse - 2 x $25 = $50"""
    
    print("Testing extractor with sample text...")
    result = extractor.extract(test_text)
    
    print("\n" + "="*50)
    print("📊 EXTRACTION RESULTS")
    print("="*50)
    
    for key, value in result.items():
        if key == "line_items":
            print(f"\n{key}:")
            for item in value:
                print(f"  {item}")
        else:
            print(f"{key}: {value}")
    
    # Verify results
    print("\n" + "="*50)
    print("✅ VERIFICATION:")
    print("="*50)
    
    checks = [
        (result["invoice_number"] == "INV-2024-001", "invoice_number should be INV-2024-001"),
        (result["vendor_name"] == "Acme Corp", "vendor_name should be Acme Corp"),
        (result["total_amount"] == 1250.0, "total_amount should be 1250.0"),
        (len(result["line_items"]) == 2, "Should have 2 line items")
    ]
    
    for passed, message in checks:
        if passed:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")