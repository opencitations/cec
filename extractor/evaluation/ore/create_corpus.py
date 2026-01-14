import re
import subprocess
import os
import zipfile

import requests
import shutil

from lxml import etree
from lxml.etree import XMLSyntaxError
from pathlib import Path
import logging
from pathlib import Path
from subprocess import TimeoutExpired  # only if transform_jats_to_tei may raise this


def transform_jats_to_tei(input_xml, output_xml, saxon_path, timeout=180, xslt_path='jats-to-tei.xsl'):
    try:
        cmd = [
            'java',
            '-jar', saxon_path,
            f'-s:{input_xml}',
            f'-xsl:{xslt_path}',
            f'-o:{output_xml}'
        ]
        print("Running:", ' '.join(cmd))
        subprocess.run(cmd, check=True, timeout=timeout)  # Added timeout parameter
        print("✅ Transformation complete.")
    except subprocess.TimeoutExpired:
        print(f"⏱️ Transformation timed out after {timeout}s")
        raise  # Re-raise to be caught by outer loop
    except subprocess.CalledProcessError as e:
        print("❌ Saxon error:", e)
        raise  # Re-raise to be caught by outer loop


def fix_whitespaces_empty_tags(input_xml):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(input_xml, parser)
    root = tree.getroot()

    ws_re = re.compile(r'\s+')

    for elem in root.iter():
        # Normalize element text (only if not pure whitespace)
        if elem.text and elem.text.strip():
            elem.text = ws_re.sub(" ", elem.text).strip()
        # Normalize tail text (but skip indentation-only tails)
        if elem.tail and elem.tail.strip():
            elem.tail = ws_re.sub(" ", elem.tail).strip()

    # Remove empty tags (no text, no children, no attributes)
    for elem in list(root.iter()):  # make static copy because we might modify
        if (
                (elem.text is None or not elem.text.strip()) and
                len(elem) == 0 and
                len(elem.attrib) == 0
        ):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    tree.write(input_xml,
                   encoding="UTF-8",
                   xml_declaration=True,
                   pretty_print=True)

def fix_multi_references(input_xml):
    # Load from file
    try:
        tree = etree.parse(input_xml)
    except etree.XMLSyntaxError as e:
        print(f"❌ Skipping invalid XML: {input_xml}")
        print(f"   Reason: {e}")
        return  # skip this file

    root = tree.getroot()


    # Iterate over all elements
    elements = list(root.iter())
    for i, elem in enumerate(elements):
        if i + 1 < len(elements):
            next_elem = elements[i + 1]
            if (elem.tag.endswith("ref") and elem.get("type") == "bibr" and elem.tail is not None and elem.tail.strip()
                    in ['-', '–', '–'] and next_elem.tag.endswith("ref") and next_elem.get("type") == "bibr"):
                start = elem.text
                end = elem.text
                if start.isdigit() and end.isdigit():
                    start = int(elem.text)
                    end = int(next_elem.text)

                    parent = elem.getparent()
                    insert_pos = parent.index(elem) + 1  # insert right after the first <ref>

                    # Insert new <ref> elements for the numbers between start and end
                    for num in range(start + 1, end):
                        new_ref = etree.Element(elem.tag, type="bibr", nsmap=elem.nsmap)
                        new_ref.text = str(num)
                        new_ref.set("target", f"#ref-{num}")

                        # Insert new_ref after elem
                        parent.insert(insert_pos, new_ref)
                        insert_pos += 1

                    # Remove the dash from tail
                    elem.tail = None

        # Save the modified XML
        tree.write(input_xml, encoding="utf-8", xml_declaration=True, pretty_print=True)


def get_latest_xml_versions(folder_path):
    folder_path = Path(folder_path)
    pattern = re.compile(r"(.+)_v(\d+)_xml\.xml$", re.IGNORECASE)

    versions = {}  # {basename: (version_number, Path)}

    for xml_file in list(folder_path.glob("*.xml")):
        match = pattern.match(xml_file.name)
        if not match:
            continue

        base, version = match.group(1), int(match.group(2))

        # keep only the newest version
        if base not in versions or version > versions[base][0]:
            versions[base] = (version, xml_file)

    # Extract only the Path objects
    return [info[1] for info in versions.values()]



def download_pdf_from_xml(xml_file, download_folder, saxon_path, xslt_path):
    Path(download_folder).mkdir(exist_ok=True)
    print(f"\n📄 Processing: {xml_file}")

    # --- Determine folder name early (to check if already processed) ---
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
    except Exception:
        # Even if the XML is invalid, we try to use its filename as folder name
        folder_name = os.path.splitext(os.path.basename(str(xml_file)))[0]
    else:
        doi_element = root.find(".//article-id[@pub-id-type='doi']")
        if doi_element is not None and doi_element.text:
            folder_name = doi_element.text.replace("/", "_")
        else:
            folder_name = os.path.splitext(os.path.basename(str(xml_file)))[0]

    # Paths for processed files
    folder_path = os.path.join(download_folder, folder_name)
    tei_path = os.path.join(folder_path, f"{folder_name}_TEI.xml")

    # ---- RESUME CHECK ----
    if os.path.exists(tei_path):
        print(f"⏩ Already processed. Skipping: {xml_file}")
        return

    # If folder exists but TEI missing → continue processing
    os.makedirs(folder_path, exist_ok=True)

    # --- Now re-parse XML (safe) ---
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
    except XMLSyntaxError as e:
        print(f"❌ XML syntax error in {xml_file}: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error reading {xml_file}: {e}")
        return

    ns = {'xlink': 'http://www.w3.org/1999/xlink'}

    # ---- 1️⃣ Locate PDF URL ----
    try:
        pdf_element = root.find(".//self-uri[@content-type='pdf']", namespaces=ns)
    except Exception as e:
        print(f"❌ Error searching XML elements: {e}")
        return

    if pdf_element is None:
        print("⚠️ No PDF link found in this XML.")
        return

    pdf_url = pdf_element.get('{http://www.w3.org/1999/xlink}href')
    if not pdf_url:
        print("⚠️ PDF element found, but no xlink:href.")
        return

    print(f"🔗 PDF URL found: {pdf_url}")

    pdf_path = os.path.join(folder_path, f"{folder_name}.pdf")

    # ---- 3️⃣ Download PDF safely ----
    if not os.path.exists(pdf_path):
        try:
            print(f"⬇️ Downloading PDF from {pdf_url} ...")
            response = requests.get(pdf_url, stream=True, timeout=30)

            if response.status_code != 200:
                print(f"❌ Failed to download PDF. HTTP {response.status_code}")
            else:
                with open(pdf_path, "wb") as f:
                    for chunk in response.iter_content(8192):
                        f.write(chunk)
                print(f"✅ Saved PDF: {pdf_path}")

        except Exception as e:
            print(f"❌ Error downloading PDF: {e}")
    else:
        print("⏩ PDF already downloaded. Skipping download.")

    # ---- 4️⃣ Copy original XML ----
    jats_path = os.path.join(folder_path, f"{folder_name}_JATS.xml")

    if not os.path.exists(jats_path):
        try:
            shutil.copy(str(xml_file), jats_path)
            print(f"📄 Copied JATS to {jats_path}")
        except Exception as e:
            print(f"❌ Error copying JATS file: {e}")
    else:
        print("⏩ JATS already copied. Skipping.")

    # ---- 5️⃣ Transform JATS → TEI ----
    try:
        transform_jats_to_tei(
            xml_file,
            tei_path,saxon_path=saxon_path,
            xslt_path=xslt_path
        )
        fix_multi_references(tei_path)
        fix_whitespaces_empty_tags(tei_path)
        print(f"📝 Created TEI: {tei_path}")

    except Exception as e:
        print(f"❌ Error generating TEI file: {e}")

def group_PDFs_for_CEX(output_folder, modified_PDFs_folder, corpus_folder):
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)
    modified_PDFs_folder = Path(modified_PDFs_folder)
    corpus_folder = Path(corpus_folder)

    # Collect paths
    all_pdfs = list(corpus_folder.rglob("*.pdf"))
    modified_pdfs = list(modified_PDFs_folder.glob("*.pdf"))

    # Copy modified PDFs first
    for pdf in modified_pdfs:
        shutil.copy2(pdf, output_folder / pdf.name)

    # Determine which original PDFs were NOT modified
    modified_names = {pdf.name for pdf in modified_pdfs}

    missing_pdfs = [pdf for pdf in all_pdfs if pdf.name not in modified_names]

    # Copy missing PDFs to output
    for pdf in missing_pdfs:
        shutil.copy2(pdf, output_folder / pdf.name)

    print(f"Copied {len(modified_pdfs)} modified PDFs.")
    print(f"Added {len(missing_pdfs)} missing PDFs from corpus.")
    print(f"Total PDFs in output: {len(list(output_folder.glob('*.pdf')))}")

def organize_PDFs_notes(corpus_folder, all_pdfs_zip, output_folder):
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    # Subfolders
    out_ref_and_notes = output_folder / "ref_and_notes"
    out_ref = output_folder / "ref"
    out_notes = output_folder / "notes"
    out_to_ignore = output_folder / "no_ref_no_notes"
    for folder in [out_ref_and_notes, out_ref, out_notes, out_to_ignore]:
        folder.mkdir(exist_ok=True)

    # List PDFs in ZIP
    with zipfile.ZipFile(all_pdfs_zip) as z:
        pdfs = {Path(name).stem: name for name in z.namelist() if name.lower().endswith(".pdf")}

        xml_folder = Path(corpus_folder)
        xml_files = list(xml_folder.rglob("*JATS.xml"))

        for xml_file in xml_files:
            try:
                tree = etree.parse(xml_file)
                root = tree.getroot()
                ns = {'xlink': 'http://www.w3.org/1999/xlink'}

                back = root.find(".//back", namespaces=ns)
                references_section = None
                notes_section = None

                if back is not None:
                    references_section = back.find("ref-list", namespaces=ns)
                    notes_nodes = back.xpath("fn-group[not(@*)]", namespaces=ns)
                    notes_section = notes_nodes[0] if notes_nodes else None

                # Find the corresponding PDF by matching the stem name
                xml_stem = xml_file.stem.replace("_JATS", "")
                pdf_name_in_zip = pdfs.get(xml_stem)

                if not pdf_name_in_zip:
                    print(f"⚠️ PDF for {xml_file.name} not found in ZIP.")
                    continue

                # Read PDF bytes from ZIP
                pdf_bytes = z.read(pdf_name_in_zip)

                # Determine target folder
                if references_section is None and notes_section is None:
                    print(f"📄 No notes and no reference sections found in {xml_file.name}")
                    target_path = out_to_ignore / f"{xml_stem}.pdf"
                elif references_section is None and notes_section:
                    print(f"📄 Just notes section found in {xml_file.name}")
                    target_path = out_notes / f"{xml_stem}.pdf"
                elif references_section and notes_section:
                    print(f"📄 Both reference section and notes found in {xml_file.name}")
                    target_path = out_ref_and_notes / f"{xml_stem}.pdf"
                elif references_section and notes_section is None:
                    print(f"📄 Just reference section found in {xml_file.name}")
                    target_path = out_ref / f"{xml_stem}.pdf"

                # Write PDF bytes to the target folder
                with open(target_path, "wb") as f:
                    f.write(pdf_bytes)

            except XMLSyntaxError as e:
                print(f"❌ XML syntax error in {xml_file}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error reading {xml_file}: {e}")


