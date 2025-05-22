import os
import requests
import lxml.etree as ET
from django.conf import settings
from .grobid_auth import get_id_token

# Adjust if GROBID is at a different base URL/port
#GROBID_FULLTEXT_URL = "http://localhost:8070/api/processFulltextDocument"

# def grobid_extract_methods(pdf_path):
#     """
#     Calls GROBID to process the full text of a PDF, then searches the resulting TEI XML
#     for a 'methods' section. Returns a single string containing all text (including
#     any equations GROBID recognized as text) from that section.
#
#     We do not do any bounding-box OCR or advanced math extraction here. We rely on
#     whatever textual representation GROBID provides, which may be imperfect for equations.
#     """
#
#     # 1) Verify PDF file existence
#     if not os.path.exists(pdf_path):
#         raise FileNotFoundError(f"PDF file not found: {pdf_path}")
#
#     # 2) Send PDF to GROBID's processFulltextDocument endpoint
#     with open(pdf_path, 'rb') as f:
#         files = {'input': (os.path.basename(pdf_path), f, 'application/pdf')}
#         params = {
#             'consolidateHeader': 1,     # tries to enrich header metadata
#             'consolidateCitations': 0,  # references consolidation not mandatory here
#             'segmentation': 'detailed', # more granular segmentation
#             'generateTeiIds': 1,
#             # We can omit teiCoordinates since we aren't doing bounding-box math
#         }
#         response = requests.post(GROBID_FULLTEXT_URL, files=files, params=params)
#         if response.status_code != 200:
#             raise Exception(f"GROBID error: {response.status_code} - {response.text}")
#
#     # 3) Parse the returned TEI XML
#     tei_xml = response.text
#     methods_text = parse_tei_for_methods(tei_xml)
#     return methods_text

def grobid_extract_methods(pdf_path):
    """
    Calls GROBID's /api/processFulltextDocument endpoint with multipart/form-data:
      - field name 'input'
      - Accept: application/xml
    Then parses the TEI XML to find 'methods' sections or a 'div' whose head is 'method'.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Fetch base URL and token for service-to-service auth
    grobid_base = getattr(settings, "GROBID_BASE_URL", "")
    if not grobid_base:
        raise ValueError("No GROBID_BASE_URL set in Django settings.")
    token = get_id_token(grobid_base)

    # Set headers with ID token + prefer TEI XML
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml"
    }

    # POST the PDF as multipart/form-data under key 'input'
    with open(pdf_path, "rb") as f:
        files = {"input": (os.path.basename(pdf_path), f, "application/pdf")}
        params = {
            "consolidateHeader": 1,
            "consolidateCitations": 0,
            "segmentation": "detailed",
            "generateTeiIds": 1
        }
        response = requests.post(
            f"{grobid_base}/api/processFulltextDocument",
            files=files,
            params=params,
            headers=headers,
            timeout=120
        )
        if response.status_code != 200:
            raise Exception(f"GROBID error: {response.status_code} - {response.text}")

    tei_xml = response.text
    # Optional debug:
    print("DEBUG => TEI excerpt:", tei_xml[:2000], "...")
    return parse_tei_for_methods(tei_xml)


# def parse_tei_for_methods(tei_xml):
#     """
#     Parses GROBID's TEI XML to find the 'methods' section text. We look for:
#       - <div type="method" or type="methods">
#       - If not found, we look for a <div><head> containing 'method'
#     We gather *all* text in that div (including <formula> as plain text),
#     returning a single combined string.
#     """
#
#     root = ET.fromstring(tei_xml.encode('utf-8'))
#
#     # 1) Attempt direct <div type="method" or "methods">
#     divs = root.findall('.//{*}div[@type="method"]')
#     divs += root.findall('.//{*}div[@type="methods"]')
#
#     # 2) If none found, fallback to any <div> whose <head> contains "method"
#     if not divs:
#         all_divs = root.findall('.//{*}div')
#         for d in all_divs:
#             head_el = d.find('{*}head')
#             if head_el is not None:
#                 head_text = (head_el.text or '').lower()
#                 if 'method' in head_text:
#                     divs.append(d)
#
#     # Combine text from all matched divs
#     collected_text = []
#     for d in divs:
#         # We'll gather all text in the div (including <formula> text if present)
#         div_text = ''.join(d.itertext()).strip()
#         if div_text:
#             collected_text.append(div_text)
#
#     return '\n\n'.join(collected_text)

def parse_tei_for_methods(tei_xml):
    """
    Parses GROBID's TEI XML to find the 'methods' section text. We look for:
      - <div type="method" or type="methods">
      - If not found, we look for a <div><head> containing 'method'
    We gather *all* text in that div (including <formula> text if present).
    """
    root = ET.fromstring(tei_xml.encode('utf-8'))

    # 1) Attempt direct <div type="method" or "methods">
    divs = root.findall('.//{*}div[@type="method"]')
    divs += root.findall('.//{*}div[@type="methods"]')

    # 2) If none found, fallback to any <div> whose <head> contains "method"
    if not divs:
        all_divs = root.findall('.//{*}div')
        for d in all_divs:
            head_el = d.find('{*}head')
            if head_el is not None:
                head_text = (head_el.text or '').lower()
                if 'method' in head_text:
                    divs.append(d)

    # Combine text from all matched divs
    collected_text = []
    for d in divs:
        div_text = ''.join(d.itertext()).strip()
        if div_text:
            collected_text.append(div_text)

    return '\n\n'.join(collected_text)
