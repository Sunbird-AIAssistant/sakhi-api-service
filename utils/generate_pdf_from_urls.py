import pdfkit
from PyPDF2 import PdfMerger
import os
import shutil

# List of URLs to convert to PDF
urls = [] # For ex.: ["https://ed.sunbird.org/", "https://ed.sunbird.org/learn"]

# Output directory where PDFs will be saved
output_directory = "output_pdfs/"

# Ensure the output directory exists or create it if it doesn't
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Output merged PDF filename
merged_pdf = "all_merged.pdf"

# # Configure options for pdfkit (e.g., page size, orientation, etc.)
options = {
    'page-size': 'A4',
    'orientation': 'Portrait'
}

# # Convert URLs to PDFs
for i, url in enumerate(urls):
    pdfkit.from_url(url, os.path.join(output_directory, f"page_{i+1}.pdf"), options=options)
    print("Converted URL to PDF === ", os.path.join(output_directory, f"page_{i+1}.pdf"))

print("PDFs generated successfully.")

# List of PDFs to merge
pdf_files = [os.path.join(output_directory, f"page_{i+1}.pdf") for i in range(len(urls))]

# Merge PDFs using PdfMerger
pdf_merger = PdfMerger()

for pdf_file in pdf_files:
    print("Merged ---", pdf_file)
    pdf_merger.append(pdf_file)

# Write the merged PDF to the output file
with open(merged_pdf, 'wb') as merged_file:
    pdf_merger.write(merged_file)

print("PDFs merged successfully.")

# Delete the output directory
shutil.rmtree(output_directory)

print(f"Output directory '{output_directory}' deleted.")