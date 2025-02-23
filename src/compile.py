import json
import numpy as np

index_template_path = "../templates/index_template.html"

pubs_insert_marker = "<!-- PUBS HERE -->"

pubs_json_path = "pubs.json"

out_path = "../index.html"


def load_index_template(index_template_path):
    with open(index_template_path) as f:
        raw_text = "".join(f.readlines())

    assert pubs_insert_marker in raw_text, raw_text

    before_pubs, after_pubs = raw_text.split(pubs_insert_marker)
    return before_pubs, after_pubs


def load_json(json_path):
    with open(json_path) as f:
        loaded_data = json.load(f)
    return loaded_data

pubs_json = load_json(pubs_json_path)


### All the transformations we will step-wise apply to the raw text
### of a pub citation to make it nice html

def bold_name(text):
    return text.replace("Cochran, K.", "<strong>Cochran, K.</strong>")

def italicize_cis(text):
    return text.replace("cis-", "<em>cis-</em>")

def wrap_in_p(text):
    prefix = '<p class="border border-special">' + "\n"
    suffix = "\n</p>"
    return prefix + text + suffix


def _find_title_start_by_year_end(text):
    possible_years = [str(year) for year in range(2018, 2030)] # will...update one day
    years_in_text = [year for year in possible_years if year in text]
    
    if len(years_in_text) == 0:
        best_year = years_in_text[0]
    else:
        # in case a page number or something matches
        locations_of_years = [text.index(year) for year in years_in_text]
        best_year = years_in_text[np.argmin(locations_of_years)]

    # +6 is assuming period and space after year
    return text.index(best_year) + 6 


def style_title_and_journal(text):
    # get index of start of title
    title_start = _find_title_start_by_year_end(text)
    # get index of first . after title start (end of title)
    title_end = text.find(".", title_start) + 1

    title_str = text[title_start:title_end]
    title_str_with_mark = "<mark>" + title_str + "</mark>"

    # repeat with the journal name (assume it's right after title)
    journal_start = title_end + 1

    # sometimes it's "bioRxiv." and other times it's "Genome Research, pp."
    journal_end = text.find(".", journal_start) + 1
    if "pp." in text[journal_start:journal_end]:
        journal_end = text.find(",", journal_start) + 1
    
    journal_str = text[journal_start:journal_end]
    journal_str_with_em = "<em>" + journal_str + "</em>"

    text = text.replace(title_str, title_str_with_mark)
    text = text.replace(journal_str, journal_str_with_em)
    return text


def _make_button_str(label, link):
    s = '<button type="button" class="btn btn-pub btn-outline-light">'
    s += '<a href="' + link + '">' + label + '</a></button>'
    return s

def add_link_buttons(text, links_dict):
    if len(links_dict) == 0:
        return text
    
    first_button = True
    for link_label, link in links_dict.items():
        button_str = _make_button_str(link_label, link)
        str_to_replace = "[" + link_label + "]"

        if first_button:
            button_str = "<br>\n" + button_str
            first_button = False

        text = text.replace(str_to_replace, "\n" + button_str)

    return text



def htmlify_pubs(pubs_json):
    html_str_list = []
    for pub_info in pubs_json:
        text, links = list(pub_info.items())[0]
        text_with_html = bold_name(italicize_cis(wrap_in_p(style_title_and_journal(text))))
        text_with_buttons = add_link_buttons(text_with_html, links)
        html_str_list.append(text_with_buttons)

    return "\n".join(html_str_list)

pubs_in_html = htmlify_pubs(pubs_json)

html_prefix, html_suffix = load_index_template(index_template_path)

full_index_html = html_prefix + pubs_in_html + html_suffix

with open(out_path, "w") as f:
    f.write(full_index_html)
