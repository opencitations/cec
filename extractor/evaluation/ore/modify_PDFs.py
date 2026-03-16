from pathlib import Path
from lxml import etree
import shutil
import os
from pypdf import PdfReader, PdfWriter
from torch.mps.profiler import start


def copy_PDF_to_modify(folder_path, output_path):
    root_path = Path(folder_path)
    Path(output_path).mkdir(exist_ok=True)

    for entry in root_path.rglob("*_JATS.xml"):
        try:
            tree = etree.parse(entry)
            xml_root = tree.getroot()

            reviewer_reports = xml_root.find(
                ".//sub-article[@article-type='reviewer-report']"
            )

            if reviewer_reports:
                # Search only the same folder as the XML
                pdf_files = list(entry.parent.glob("*.pdf"))

                if pdf_files:
                    pdf_file = pdf_files[0]
                    dest = Path(output_path) / pdf_file.name
                    shutil.copy(pdf_file, dest)
                    print(f"✔ Copied: {pdf_file.name}")
                else:
                    print(f"⚠ No PDF found in: {entry.parent}")

        except etree.XMLSyntaxError as e:
            print(f"❌ XML syntax error in {entry}: {e}")

        except Exception as e:
            print(f"❌ Unexpected error in {entry}: {e}")


from pypdf import PdfReader, PdfWriter
from pathlib import Path


def remove_open_peer_review(input_pdf, output_pdf, log_file, keyword="open peer review"):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    keyword = keyword.lower()
    remove_from = None
    filename = Path(input_pdf).name

    # 1. Identify the first page containing "Open Peer Review"
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").lower()
        if keyword in text and i != 0:
            remove_from = i
            print(f"{filename}: Found '{keyword}' on page {i+1}. Removing page {i+1} onward.")
            break

    # 2. If not found: copy whole document
    if remove_from is None:
        msg = f"{filename}: No 'Open Peer Review' section found. PDF unchanged.\n"

        with open(output_pdf, "wb") as f:
            writer.append_pages_from_reader(reader)

        with open(log_file, "a") as log:
            log.write(msg)
        return

    # 3. Copy pages BEFORE that one
    for i in range(remove_from):
        writer.add_page(reader.pages[i])

    # 4. Save the cleaned PDF
    with open(output_pdf, "wb") as f:
        writer.write(f)

    # 5. Write log entry
    msg = f"{filename}: Removed pages from {remove_from + 1} to {len(reader.pages)}\n"
    with open(log_file, "a") as log:
        log.write(msg)

def keep_pages(input_pdf, output_pdf, pages_range_to_keep):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    total = len(reader.pages)

    for range_pages in pages_range_to_keep:
        start_page = int(range_pages.split("-")[0])
        end_page = int(range_pages.split("-")[1])

        for i in range(total):
            if start_page <= i <= end_page:
                writer.add_page(reader.pages[i])
    # Save output
    with open(output_pdf, "wb") as f:
        writer.write(f)

