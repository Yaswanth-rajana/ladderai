from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Create a simple test invoice
c = canvas.Canvas("test_invoice.pdf", pagesize=letter)
c.drawString(100, 750, "INVOICE")
c.drawString(100, 700, "Invoice No: INV-2024-001")
c.drawString(100, 680, "Date: 2024-03-15")
c.drawString(100, 660, "Vendor: Acme Corp")
c.drawString(100, 640, "Total Amount: $1,250.00")
c.drawString(100, 620, "Tax: $100.00")
c.drawString(100, 580, "Line Items:")
c.drawString(100, 560, "1. Laptop - 1 x $1000 = $1000")
c.drawString(100, 540, "2. Mouse - 2 x $25 = $50")
c.save()

print("Created test_invoice.pdf")