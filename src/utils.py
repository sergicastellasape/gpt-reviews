import os
import json
import feedparser
import logging
import requests
import PyPDF2

from src.writing import generate


def load_content():
    """parses the stuff in content.txt + crawls necessary data into json
    The important thing here is to convert something that easy to edit by a human
    (the .txt) into something that's convenient for later use. This could benefit
    from unification in the papers vs. news/other content types... but not yet.
    
    IMPORTANT: the structure of the text needs to be
    - elements are separated by ---
    - first line is the type of doc [NEWS]/[PAPER]/[OTHER]"""

    type_map = {"[NEWS]": "news",
                "[PAPER]": "paper",
                "[OTHER]": "other"}
    
    if not os.path.exists(f"assets-today/content.json"):
        logging.info("Parsing content from content.txt")
        with open("content.txt") as f:
            content_list = f.read().split("---")
        # make sure no empty stuff
        content_list = [c.strip() for c in content_list if c.strip()]
        content = []
        for item in content_list:
            # we just delete empty lines. FRUGAL ON TOKENS!!!!!
            sentences = [s.strip() for s in item.split("\n") if s.strip()]
            # the pop() is convenient but i'm not sure i like it...
            # it's changing the state of sentences, then the index 0 will be the
            # title or URL.. it's convenient
            type_ = type_map[sentences.pop(0)]
            if type_ == "paper":
                id = sentences[0].split("/")[-1]
                content.append({
                    "type": type_,
                    **get_arxiv_metadata(id, parse_orgs=True),
                    "extra_content": "\n".join(sentences[1:])
                    })
            elif type_ in ["news", "other"]:
                content.append({
                    "type": type_,
                    "title": sentences[0],
                    "source": sentences[1],
                    "url": sentences[2],
                    "content": "\n".join(sentences[3:])})
                
        with open(f"assets-today/content.json", "w") as f:
            json.dump(content, f)
    else:
        logging.info("Loading content from content.json")
        with open(f"assets-today/content.json") as f:
            content = json.load(f)
    return content


def get_arxiv_metadata(id, parse_orgs=True):
    """Given an arxiv id it returns the metadata for title, authors, orgs, url, and abstract.
    Can download the pdf + extract orgs from it with the chatGPT api. Slows down the whole thing
    cause downloading Computer Vision paper pdfs is slow, but it works like a charm."""
    assert len(id) == 10, id
    # yeah we do 1 call per id when we could do batched ones for all
    # ids. But this is more clean and we're only doing ~3 paper per day
    # so the cost is assumable
    arxiv_feed = feedparser.parse(f"https://export.arxiv.org/api/query?id_list={id}")

    metadata = arxiv_feed['entries'][0]
    authors = [d["name"] for d in metadata["authors"]]
    orgs = get_org_from_id(id) if parse_orgs else ""

    paper = {"title": metadata["title"].replace("\n", " "),
             "authors": ", ".join(authors),
             "orgs": orgs,
             "url": f"https://arxiv.org/abs/{id}",
             "abstract": metadata["summary"] }
    return paper


def get_org_from_id(id):
    # Gets orgs from parsing + openais
    # bit hacky cause i wanna generalize this to
    # more content but it's okay for now
    fname = f"assets-today/pdfs/{id}.pdf"
    if not os.path.exists(fname):
        url = f"https://arxiv.org/pdf/{id}.pdf"
        response = requests.get(url)
        with open(fname, 'wb') as f:
            f.write(response.content)
    with open(fname, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = reader.pages[0].extract_text()
        prompt = f"{text}\n\n --- \nList in comma-separated form, the universities, institutions, and/or companies that participated in the paper above. Use Short names."
        orgs = generate("", prompt, temperature=0)
    return orgs

