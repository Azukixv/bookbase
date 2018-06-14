from tools.DocIndex import GutenbergIndexSchema
from tools.WebParser import GutenbergParser
from whoosh.index import *
import os
import requests
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_GUTENBERG_DIR = os.path.join(ROOT, 'data', 'gutenberg')
INDEX_GUTENBERG_DIR = os.path.join(ROOT, 'index', 'gutenberg')


def keep_get(url):
    keep_alive = True
    while keep_alive:
        try:
            result = requests.get(url)
            keep_alive = False
        except Exception:
            print('LINK REESTABLISHMENT')
            time.sleep(1)
    return result


def gutenberg_doc_crawler(index):
    parser = GutenbergParser()
    book_url = 'https://www.gutenberg.org/ebooks/' + str(index)
    response = keep_get(book_url)
    if response.status_code != 200:
        return None
    else:
        html = response.content.decode('utf-8')
        parser.feed(html)

        if parser.content_url == '':
            with open('bookbase.excpt', 'a', encoding='utf-8') as excpt:
                log = '[Gutenberg]:\thttp://www.gutenberg.org/ebooks/%d did not get text url\n' % index
                excpt.write(log)
            return None

        if parser.language != 'en':
            with open('bookbase.excpt', 'a', encoding='utf-8') as excpt:
                log = '[Gutenberg]:\thttp://www.gutenberg.org/ebooks/%d not an English article\n' % index
                excpt.write(log)
            return None
        else:
            if parser.content_url[:4] != 'http':
                parser.content_url = 'http:' + parser.content_url

            try:
                text = keep_get(parser.content_url)
                text = text.content.decode('utf-8-sig', 'ignore')
                parser.content = text
            except Exception as e:
                with open('bookbase.excpt', 'a', encoding='utf-8') as excpt:
                    log = '[Gutenberg] %s:\t%s\n' % (str(index), str(e))
                    excpt.write(log)
                return None

    filename = '%s.book' % os.path.join(DATA_GUTENBERG_DIR, str(index))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
        print('BOOK %d SAVED' % index)

    return parser


def gutenberg_index_build(parser):
    writer = open_dir(INDEX_GUTENBERG_DIR).writer()
    writer.add_document(
        title=parser.title,
        author=parser.author,
        date=parser.date,
        content=parser.content
    )
    writer.commit()


if __name__ == '__main__':
    if not os.path.exists(DATA_GUTENBERG_DIR):
        os.makedirs(DATA_GUTENBERG_DIR)

    if not os.path.exists(INDEX_GUTENBERG_DIR):
        schema = GutenbergIndexSchema()
        os.makedirs(INDEX_GUTENBERG_DIR)
        create_in(INDEX_GUTENBERG_DIR, schema)

    for index in range(1, 11):
        parser = gutenberg_doc_crawler(index)
        gutenberg_index_build(parser)
        sleep(5)
