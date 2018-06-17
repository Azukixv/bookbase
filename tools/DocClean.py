import re


def clean_gutenberg_doc(text):
    text = re.sub(r'[\n\r]+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9\']+', ' ', text)
    clean_re = r'.* START OF THIS PROJECT GUTENBERG EBOOK (.*)End of .* Project Gutenberg .*'
    clean_pattern = re.compile(clean_re)
    return clean_pattern.match(text)