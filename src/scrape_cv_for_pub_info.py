import pdftotext
import json
import pypdf
from collections import defaultdict


KEY_PUBS_TO_INCLUDE = ["Dissecting the cis-regulatory syntax of transcription initiation",
                       "Domain-adaptive neural networks",
                       "Comprehensive identification of mRNA isoforms"]

cv_pdf_path = "../CV.pdf"

out_path = "pubs.json"

# text delimiters for where the publications section starts and ends
where_pubs_start = "KEY PAPERS"
where_pubs_end = "ADDITIONAL PAPERS"



### STEP 1: Parse PDF text

# Load PDF
with open(cv_pdf_path, "rb") as f:
    pdf_raw_text_by_page = pdftotext.PDF(f)

# first, just get all text
whole_raw_text = "\n".join(pdf_raw_text_by_page)

# second, get just the section with pubs
pubs_raw_text = whole_raw_text.split(where_pubs_start)[1].split(where_pubs_end)[0]



### STEP 2: Process raw PDF text into list of publication citations

def organize_text_lines(pubs_raw_text):
    # converts messy lines of text, randomly split up, into
    # list where each element is all the text for 1 pub.

    # list to return
    pubs_text = []

    # current string of pub info we are adding to
    curr_pub = ""

    # iterate over lines of raw text
    lines = pubs_raw_text.split("\n")
    for line_i, line in enumerate(lines):
        line = line.strip()

        # if we reach empty line, we might be at end of a pub
        if len(line) == 0:
            if len(curr_pub) > 0:
                pubs_text.append(curr_pub)
                curr_pub = ""
            continue

        # skip if style line ("-----") or page number footer
        if set(line) == set(["—"]) or "Kelly Cochran" in line:
            continue

        # pubs USUALLY end with [Preprint] or [Code] or similar,
        # so when we see a line ending with ], it's the end of a pub
        if line.endswith("]"):
            curr_pub += line + " "

            # if a pub has multiple [..] [..], keep appending;
            # else (case below, see "not"), handle like end
            if not (line_i < len(lines) -1 and lines[line_i + 1].endswith("]")):
                pubs_text.append(curr_pub)
                curr_pub = ""
        else:
            curr_pub += line + " "

    return pubs_text


pubs_text = organize_text_lines(pubs_raw_text)



### STEP 3: Pull links in pub info out of PDF

# (apparently associating links w/ text directly is not doable)
# (needs a whole second libary)
# (but don't switch to pypdf for everything, it's bad at text parsing)

def get_first_page_num_with_keyword(pdf_raw_text_by_page, keyword=where_pubs_start):
    # find the first page with publication info on it
    for page_num, page_text in enumerate(pdf_raw_text_by_page):
        if keyword in page_text:
            return page_num 


def load_all_links(cv_pdf_path, where_pubs_start = where_pubs_start):
    # parses the pdf by pulling links instead of text

    # we start on the pubs page to skip the random links on page 1
    start_page = get_first_page_num_with_keyword(pdf_raw_text_by_page,
                                                 keyword=where_pubs_start)

    links = []
    for page_num, page in enumerate(pypdf.PdfReader(cv_pdf_path).pages):
        if page_num < start_page:
            continue

        if "/Annots" in page.keys():
            annotations = page["/Annots"]
            for annot in annotations:
                if "/URI" in annot["/A"].keys():
                    links.append(annot["/A"]["/URI"])

    return links

all_links = load_all_links(cv_pdf_path)


def get_text_between_brackets(text):
    if not ("[" in text and "]" in text):
        return ""
    
    text_between = []
    while "[" in text and "]" in text:
        start = text.index("[") + 1
        end = text.index("]")
        between = text[start:end]

        text_between.append(between)
        text = text[end + 1 :]

    return text_between


def associate_links_with_pubs(pubs_text, all_links):
    # make dictionary from pub info to {dict of related links},
    # where the inner dict is (key = label string, value = url string)

    pubs_to_links = defaultdict(lambda : dict())
    for pub_text in pubs_text:
        link_labels = get_text_between_brackets(pub_text)
        if len(link_labels) == 0:
            continue

        links_for_this_pub = all_links[:len(link_labels)]

        pubs_to_links[pub_text] = {label : link for label, link in zip(link_labels, links_for_this_pub)}

        all_links = all_links[len(link_labels):]

    return pubs_to_links


pubs_links = associate_links_with_pubs(pubs_text, all_links)


def filter_for_key_pubs(pubs_text, include = KEY_PUBS_TO_INCLUDE):
    to_keep = []
    for pub_text in pubs_text:
        for possible_keyphrase in include:
            if possible_keyphrase in pub_text:
                to_keep.append(pub_text)
                break
    return to_keep

# for now, only using a subset of pubs
key_pubs_text = filter_for_key_pubs(pubs_text)


# convert to dict to be able to save as json
json_dict = [{text : pubs_links[text]} for text in key_pubs_text]
pubs_json = json.dumps(json_dict, indent=4)
 
# write to file
with open(out_path, "w") as f:
    f.write(pubs_json)






