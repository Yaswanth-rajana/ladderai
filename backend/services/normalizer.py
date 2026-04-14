from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class DataNormalizer:
    def __init__(self):
        pass
    
    def normalize(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all extracted fields to consistent format
        """
        normalized = extracted_data.copy()
        
        # Normalize vendor_name (trim, capitalize properly)
        if normalized.get("vendor_name"):
            normalized["vendor_name"] = self._normalize_vendor_name(normalized["vendor_name"])
        
        # Normalize invoice_number (trim, uppercase)
        if normalized.get("invoice_number"):
            normalized["invoice_number"] = self._normalize_invoice_number(normalized["invoice_number"])
        
        # Normalize date (ensure YYYY-MM-DD)
        if normalized.get("invoice_date"):
            normalized["invoice_date"] = self._normalize_date(normalized["invoice_date"])
        
        # Normalize currency (ensure 3-letter code)
        if normalized.get("currency"):
            normalized["currency"] = self._normalize_currency(normalized["currency"])
        
        # Normalize amounts (ensure float, 2 decimal places)
        if normalized.get("total_amount"):
            normalized["total_amount"] = self._normalize_amount(normalized["total_amount"])
        
        if normalized.get("tax_amount"):
            normalized["tax_amount"] = self._normalize_amount(normalized["tax_amount"])
        
        # Normalize line items
        if normalized.get("line_items"):
            normalized["line_items"] = self._normalize_line_items(normalized["line_items"])
        
        return normalized
    
    def _normalize_vendor_name(self, name: str) -> str:
        """Clean and format vendor name"""
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name)
        # Trim
        name = name.strip()
        # Capitalize each word
        name = name.title()
        return name
    
    def _normalize_invoice_number(self, inv_num: str) -> str:
        """Clean invoice number"""
        # Remove extra spaces
        inv_num = inv_num.strip()
        # Convert to uppercase
        inv_num = inv_num.upper()
        return inv_num
    
    def _normalize_date(self, date_str: str) -> str:
        """Ensure YYYY-MM-DD format"""
        try:
            # If already in YYYY-MM-DD
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return date_str
            
            # Try DD-MM-YYYY or DD/MM/YYYY
            for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except:
                    continue
            
            return date_str
        except:
            return date_str
    
    def _normalize_currency(self, currency: str) -> str:
        """Convert to 3-letter currency code"""
        currency_map = {
            '$': 'USD',
            'USD': 'USD',
            'usd': 'USD',
            '€': 'EUR',
            'EUR': 'EUR',
            'eur': 'EUR',
            '£': 'GBP',
            'GBP': 'GBP',
            'gbp': 'GBP',
            '₹': 'INR',
            'INR': 'INR',
            'inr': 'INR'
        }
        
        return currency_map.get(currency, 'USD')
    
    def _normalize_amount(self, amount: float) -> float:
        """Round to 2 decimal places"""
        return round(amount, 2)
    
    def _normalize_line_items(self, items: List[Dict]) -> List[Dict]:
        """Normalize each line item"""
        normalized_items = []
        for item in items:
            normalized = {}
            
            # Normalize description
            if item.get("description"):
                normalized["description"] = item["description"].strip().title()
            
            # Normalize quantity
            if item.get("quantity"):
                normalized["quantity"] = round(float(item["quantity"]), 2)
            
            # Normalize unit_price
            if item.get("unit_price"):
                normalized["unit_price"] = round(float(item["unit_price"]), 2)
            
            # Normalize line_total
            if item.get("line_total"):
                normalized["line_total"] = round(float(item["line_total"]), 2)
            
            normalized_items.append(normalized)
        
        return normalized_items


# Test function
if __name__ == "__main__":
    normalizer = DataNormalizer()
    
    # Test data
    test_data = {
        "vendor_name": "  acme corp  ",
        "invoice_number": "inv-2024-001",
        "invoice_date": "15/03/2024",
        "currency": "$",
        "total_amount": 1250.000,
        "tax_amount": 100.0000,
        "line_items": [
            {
                "description": "  laptop  ",
                "quantity": 1.0,
                "unit_price": 1000.00,
                "line_total": 1000.00
            }
        ]
    }
    
    print("Original:")
    print(test_data)
    
    print("\nNormalized:")
    normalized = normalizer.normalize(test_data)
    print(normalized)