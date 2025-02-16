import os
import requests
import lxml.etree as ET

GROBID_FULLTEXT_URL = "http://localhost:8070/api/processFulltextDocument"

def grobid_extract_references(pdf_path):
    """
    Calls GROBID's /api/processFulltextDocument endpoint with various tweaks:
      - consolidateCitations=1 (try to enrich references)
      - consolidateHeader=1 (enrich header metadata)
      - includeRawCitations=1 (return raw citation text)
      - generateIDs=1 (assign unique IDs in TEI)
      - teiCoordinates='biblStruct' (coordinates for references, optional)
      - segmentation='detailed' (attempt more granular segmentation)

    Returns a list of references in dict form (first_name, last_name, title, year, journal).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        files = {
            'input': (os.path.basename(pdf_path), f, 'application/pdf')
        }
        # Here are the parameter tweaks:
        params = {
            'consolidateCitations': 1,      # Enrich references with external data
            'consolidateHeader': 1,         # Enrich header metadata
            'includeRawCitations': 1,       # Include raw citation strings in the TEI
            'generateIDs': 1,               # Generate XML IDs for elements
            'teiCoordinates': 'biblStruct', # Provide coordinates for reference structs
            'segmentation': 'detailed',     # More detailed segmentation (vs 'basic')
        }

        response = requests.post(GROBID_FULLTEXT_URL, files=files, params=params)
        if response.status_code != 200:
            raise Exception(f"GROBID error: {response.status_code} - {response.text}")

    tei_xml = response.text
    references_list = parse_tei_xml_for_references(tei_xml)
    return references_list


def parse_tei_xml_for_references(tei_xml):
    """
    Parses the TEI XML returned by GROBID to find references, typically within:
      - <div type="references">
      - <listBibl>
    Each reference is represented by <biblStruct>.

    We extract:
      - First author's forename/surname
      - Title
      - Year
      - Journal

    Returns a list of dictionaries with these fields.
    """
    root = ET.fromstring(tei_xml.encode('utf-8'))

    # Try to locate references in <div type="references"> or <listBibl>
    references_divs = root.findall('.//{*}div[@type="references"]')
    list_bibls = root.findall('.//{*}listBibl')

    bibl_structs = []
    for div in references_divs:
        bibl_structs.extend(div.findall('.//{*}biblStruct'))
    for lb in list_bibls:
        bibl_structs.extend(lb.findall('.//{*}biblStruct'))

    # Remove duplicates if any appear in both sets
    bibl_structs = list(set(bibl_structs))

    results = []
    for bibl in bibl_structs:
        authors = []
        # Extract authors under <author> elements
        for author_el in bibl.findall('.//{*}author'):
            forename_el = author_el.find('.//{*}forename')
            surname_el = author_el.find('.//{*}surname')
            if forename_el is not None and surname_el is not None:
                authors.append((forename_el.text or '', surname_el.text or ''))

        # Extract reference title
        title_el = bibl.find('.//{*}title')
        title = title_el.text if title_el is not None else ''

        # Extract year
        date_el = bibl.find('.//{*}date')
        year = ''
        if date_el is not None:
            year = date_el.get('when') or (date_el.text or '')

        # Extract journal (often under <monogr><title level="j">
        journal_el = bibl.find('.//{*}monogr/{*}title[@level="j"]')
        journal = journal_el.text if journal_el is not None else ''
        if not journal:
            alt_journal_el = bibl.find('.//{*}title[@type="journal"]')
            journal = alt_journal_el.text if alt_journal_el is not None else ''

        # Take only the first author for the table display
        first_author_first_name = ''
        first_author_last_name = ''
        if authors:
            first_author_first_name = authors[0][0].strip()
            first_author_last_name = authors[0][1].strip()

        ref_obj = {
            'first_name': first_author_first_name,
            'last_name': first_author_last_name,
            'title': (title or '').strip(),
            'year': (year or '').strip(),
            'journal': (journal or '').strip()
        }
        results.append(ref_obj)

    return results
