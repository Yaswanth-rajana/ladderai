import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def run_integration_test():
    print("📤 Uploading new invoice...")
    file_path = "test_invoice.pdf"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
        
    if response.status_code != 202:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return
        
    result = response.json()
    doc_id = result["document_id"]
    print(f"✅ Document ID: {doc_id}")
    
    # Poll for completion (though it's synchronous for now in our simplified setup)
    print("Waiting for processing...")
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/documents/{doc_id}")
    doc = response.json()
    
    print("\n📊 Extracted Data:")
    data = doc.get("extracted_data", {})
    print(f"Status: {doc['status']}")
    print(f"Vendor: {data.get('vendor_name')}")
    print(f"Invoice #: {data.get('invoice_number')}")
    print(f"Total: {data.get('total_amount')}")
    print(f"Line Items: {len(data.get('line_items', []))}")
    
    if doc['status'] == 'completed' and data.get('invoice_number') == 'INV-2024-001':
        print("\n✅ INTEGRATION TEST PASSED")
    else:
        print("\n❌ INTEGRATION TEST FAILED")

if __name__ == "__main__":
    run_integration_test()
