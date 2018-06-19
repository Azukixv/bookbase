import re


def clean_gutenberg_doc(text):
    text = re.sub(r'[\n\r]+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9\']+', ' ', text)
    clean_re = r'.* START OF THIS PROJECT GUTENBERG EBOOK (.*)End of .* Project Gutenberg .*'
    clean_pattern = re.compile(clean_re)
    return clean_pattern.match(text)


def clean_douban_review(text):
    text = re.sub(r'<[\w\s=":/.]+>', '', text)
    text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'\s+|\(展开\)', '', text)
    return text


def clean_duanwenxue_doc(text):
    clean_re = r'.*APP下载(.*)海量美文.*'
    clean_pattern = re.compile(clean_re)
    return clean_pattern.match(text)