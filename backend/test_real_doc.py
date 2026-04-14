import json
import requests
import sys
from services.extractor import InvoiceExtractor

# doc_id passed as arg
if len(sys.argv) < 2:
    print("Usage: python test_real_doc.py <doc_id>")
    sys.exit(1)

doc_id = sys.argv[1]

# Get the document
try:
    response = requests.get(f'http://localhost:8000/documents/{doc_id}')
    response.raise_for_status()
    doc = response.json()
except Exception as e:
    print(f"Error fetching document: {e}")
    sys.exit(1)

print('📄 Testing extractor on your actual document...')
print('='*50)

# Extract using the extractor
extractor = InvoiceExtractor()
result = extractor.extract(doc['extracted_text'])

print(json.dumps(result, indent=2))

# Verify key fields
print('\n' + '='*50)
print('✅ VERIFICATION:')
print('='*50)
print(f"Vendor: {result['vendor_name']}")
print(f"Invoice #: {result['invoice_number']}")
print(f"Date: {result['invoice_date']}")
print(f"Total: ${result['total_amount']}")
print(f"Tax: ${result['tax_amount']}")
print(f"Line Items: {len(result['line_items'])}")
