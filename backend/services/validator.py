from typing import Dict, Any, List, Tuple
import math
from datetime import datetime

class InvoiceValidator:
    def __init__(self):
        self.required_fields = [
            "vendor_name",
            "invoice_number", 
            "invoice_date",
            "total_amount"
        ]
        
    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[List[str], float]:
        """
        Validate extracted data and return (errors, confidence_score)
        """
        errors = []
        confidence_factors = []
        
        # 1. Check for missing required fields
        missing_fields = self._check_missing_fields(extracted_data)
        if missing_fields:
            errors.append(f"Missing fields: {', '.join(missing_fields)}")
            # Reduce confidence for each missing field
            missing_factor = 1 - (len(missing_fields) / len(self.required_fields))
            confidence_factors.append(missing_factor)
        else:
            confidence_factors.append(1.0)
        
        # 2. Validate math: sum(line_items) should equal total_amount
        math_error, math_factor = self._validate_line_item_sum(extracted_data)
        if math_error:
            errors.append(math_error)
        confidence_factors.append(math_factor)
        
        # 3. Validate date is valid and not in future
        date_error, date_factor = self._validate_date(extracted_data.get("invoice_date"))
        if date_error:
            errors.append(date_error)
        confidence_factors.append(date_factor)
        
        # 4. Validate amounts are positive
        amount_error, amount_factor = self._validate_amounts(extracted_data)
        if amount_error:
            errors.append(amount_error)
        confidence_factors.append(amount_factor)
        
        # 5. Validate line items structure
        line_items_error, line_items_factor = self._validate_line_items(extracted_data.get("line_items", []))
        if line_items_error:
            errors.append(line_items_error)
        confidence_factors.append(line_items_factor)
        
        # Calculate overall confidence (average of all factors)
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        confidence = round(confidence * 100, 1)  # Convert to percentage
        
        return errors, confidence
    
    def _check_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """Check which required fields are missing or None"""
        missing = []
        for field in self.required_fields:
            value = data.get(field)
            if value is None or value == "":
                missing.append(field)
        return missing
    
    def _validate_line_item_sum(self, data: Dict[str, Any]) -> Tuple[str, float]:
        """Check if sum of line items matches total_amount"""
        line_items = data.get("line_items", [])
        total_amount = data.get("total_amount")
        
        # If no line items, skip validation
        if not line_items:
            return None, 1.0
        
        # If total_amount is missing, can't validate
        if total_amount is None:
            return "Total amount missing, cannot validate line items", 0.5
        
        # Calculate sum of line totals
        calculated_total = 0
        for item in line_items:
            line_total = item.get("line_total")
            if line_total is not None:
                calculated_total += line_total
        
        # If no line totals found, try calculating from quantity * unit_price
        if calculated_total == 0:
            for item in line_items:
                quantity = item.get("quantity")
                unit_price = item.get("unit_price")
                if quantity is not None and unit_price is not None:
                    calculated_total += quantity * unit_price
        
        # If still 0, can't validate
        if calculated_total == 0:
            return "Could not calculate line items total", 0.3
        
        # Check if approximately equal (within 1% or $0.01)
        difference = abs(calculated_total - total_amount)
        tolerance = max(0.01, total_amount * 0.01)  # 1% or $0.01 minimum
        
        if difference <= tolerance:
            return None, 1.0
        else:
            return f"Line items sum (${calculated_total:.2f}) doesn't match total amount (${total_amount:.2f})", 0.5
    
    def _validate_date(self, date_str: str) -> Tuple[str, float]:
        """Check if date is valid and not in future"""
        if not date_str:
            return "Invoice date missing", 0.5
        
        try:
            # Parse date (assuming YYYY-MM-DD format after normalization)
            invoice_date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            
            # Check if date is in future
            if invoice_date > today:
                return f"Invoice date {date_str} is in the future", 0.3
            
            # Check if date is too old (older than 10 years)
            if (today - invoice_date).days > 3650:
                return f"Invoice date {date_str} is more than 10 years old", 0.7
            
            return None, 1.0
        except:
            return f"Invalid date format: {date_str}", 0.4
    
    def _validate_amounts(self, data: Dict[str, Any]) -> Tuple[str, float]:
        """Check if amounts are positive and reasonable"""
        total = data.get("total_amount")
        tax = data.get("tax_amount")
        
        if total is not None:
            if total <= 0:
                return f"Total amount (${total}) should be positive", 0.3
            if total > 1000000:  # Suspiciously large
                return f"Total amount (${total}) seems unreasonably high", 0.7
        
        if tax is not None:
            if tax < 0:
                return f"Tax amount (${tax}) should not be negative", 0.3
            if total and tax > total:
                return f"Tax amount (${tax}) exceeds total amount (${total})", 0.5
        
        return None, 1.0
    
    def _validate_line_items(self, line_items: List[Dict]) -> Tuple[str, float]:
        """Validate line items structure and values"""
        if not line_items:
            return None, 1.0  # No line items is acceptable
        
        errors = []
        
        for i, item in enumerate(line_items):
            quantity = item.get("quantity")
            unit_price = item.get("unit_price")
            line_total = item.get("line_total")
            
            # Check if line_total matches quantity * unit_price
            if quantity is not None and unit_price is not None and line_total is not None:
                expected = quantity * unit_price
                if abs(expected - line_total) > 0.01:
                    errors.append(f"Line item {i+1}: calculated total ${expected:.2f} doesn't match ${line_total:.2f}")
            
            # Check for negative values
            if quantity is not None and quantity < 0:
                errors.append(f"Line item {i+1}: negative quantity ({quantity})")
            if unit_price is not None and unit_price < 0:
                errors.append(f"Line item {i+1}: negative unit price (${unit_price})")
        
        if errors:
            return "; ".join(errors[:3]), 0.6  # Return first 3 errors
        return None, 1.0


# Test function
if __name__ == "__main__":
    validator = InvoiceValidator()
    
    # Test Case 1: Perfect invoice (total matches line items)
    perfect_invoice = {
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-03-15",
        "currency": "USD",
        "total_amount": 1050.00,  # Matches 1000 + 50
        "tax_amount": 100.00,
        "line_items": [
            {"description": "Laptop", "quantity": 1, "unit_price": 1000, "line_total": 1000},
            {"description": "Mouse", "quantity": 2, "unit_price": 25, "line_total": 50}
        ]
    }
    
    print("Test 1: Perfect Invoice")
    errors, confidence = validator.validate(perfect_invoice)
    print(f"  Errors: {errors}")
    print(f"  Confidence: {confidence}%")
    print()
    
    # Test Case 2: Missing fields and math error
    bad_invoice = {
        "vendor_name": "Acme Corp",
        "invoice_number": None,  # Missing
        "invoice_date": "2024-03-15",
        "total_amount": 2000.00,  # Wrong total
        "line_items": [
            {"description": "Laptop", "quantity": 1, "unit_price": 1000, "line_total": 1000},
            {"description": "Mouse", "quantity": 2, "unit_price": 25, "line_total": 50}
        ]
    }
    
    print("Test 2: Bad Invoice (missing fields, math error)")
    errors, confidence = validator.validate(bad_invoice)
    print(f"  Errors: {errors}")
    print(f"  Confidence: {confidence}%")
    print()
    
    # Test Case 3: Future date
    future_invoice = {
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2025-12-31",  # Future date
        "total_amount": 1050.00,
        "line_items": [
            {"description": "Laptop", "quantity": 1, "unit_price": 1000, "line_total": 1000},
            {"description": "Mouse", "quantity": 2, "unit_price": 25, "line_total": 50}
        ]
    }
    
    print("Test 3: Future Date")
    errors, confidence = validator.validate(future_invoice)
    print(f"  Errors: {errors}")
    print(f"  Confidence: {confidence}%")