from services.extractor import InvoiceExtractor

extractor = InvoiceExtractor()

# Test Case 1: Different invoice number format
test1 = """INVOICE
Inv #: INV-999-2024
Total: $500.00"""

print("Test 1: Different format (Inv #:)")
result = extractor.extract(test1)
print(f"  Invoice #: {result['invoice_number']}")
print(f"  Total: {result['total_amount']}")
print()

# Test Case 2: Missing tax
test2 = """INVOICE
Invoice No: ABC-123
Total Amount: $750.00"""

print("Test 2: Missing tax field")
result = extractor.extract(test2)
print(f"  Invoice #: {result['invoice_number']}")
print(f"  Total: {result['total_amount']}")
print(f"  Tax: {result['tax_amount']} (should be None)")
print()

# Test Case 3: Different date format
test3 = """INVOICE
Date: 15/03/2024
Total: $300.00"""

print("Test 3: Different date format (DD/MM/YYYY)")
result = extractor.extract(test3)
print(f"  Date: {result['invoice_date']}")
print()

# Test Case 4: No line items
test4 = """INVOICE
Invoice No: SIMPLE-001
Total: $100.00"""

print("Test 4: No line items")
result = extractor.extract(test4)
print(f"  Line items: {result['line_items']} (should be empty list)")
