from tools.DocIndex import *
from tools.WebParser import *
from tools.DocClean import *
from whoosh.index import *
import os
import shutil
import logging
import requests
import time
import queue
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_GUTENBERG_DIR = os.path.join(ROOT, 'data', 'gutenberg')
INDEX_GUTENBERG_DIR = os.path.join(ROOT, 'index', 'gutenberg')
DATA_DUANWENXUE_DIR = os.path.join(ROOT, 'data', 'duanwenxue')
INDEX_DUANWENXUE_DIR = os.path.join(ROOT, 'index', 'duanwenxue')
GUTENBERG_PARSER_QUEUE = queue.Queue()
COUNTER = [[0, 0], [0, 0]]


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
    logger = logging.getLogger('gutenberg')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler('bookbase.excpt', mode='a')
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(fh)

    parser = GutenbergParser()
    book_url = 'https://www.gutenberg.org/ebooks/' + str(index)
    parser.url = book_url
    response = keep_get(book_url)
    if response.status_code != 200:
        return None
    else:
        html = response.content.decode('utf-8')
        parser.feed(html)

        if parser.content_url == '':
            logger.info('[Gutenberg] \t%s did not get text url' % book_url)
            return None

        if parser.language != 'en':
            logger.info('[Gutenberg] \t%s not an English article' % book_url)
            return None
        else:
            if parser.content_url[:4] != 'http':
                parser.content_url = 'http:' + parser.content_url

            try:
                text = keep_get(parser.content_url)
                text = text.content.decode('utf-8-sig', 'ignore')
                match = clean_gutenberg_doc(text)
                if match:
                    parser.content = match.group(1)
                else:
                    logger.info('[Gutenberg] \t%s not meet the format' % book_url)
                    return None
            except Exception as e:
                logger.info('[Gutenberg] %s:\t%s' % (book_url, str(e)))
                return None

    filename = '%s.book' % os.path.join(DATA_GUTENBERG_DIR, str(index))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(parser.content)
        print('BOOK[EN] %d SAVED' % index)
        COUNTER[0][0] += 1

    GUTENBERG_PARSER_QUEUE.put(parser)
    return parser


def gutenberg_doc_crawler_(start, end):
    for index in range(start, end):
        gutenberg_doc_crawler(index)


def gutenberg_index_build(writer, parser):
    reviews = douban_review_crawler(parser.title)
    if reviews == None or reviews == []:
        writer.add_document(
            title=parser.title,
            author=parser.author,
            date=parser.date,
            content=parser.content,
            url=parser.url,
            tag=parser.tag
        )
    else:
        writer.add_document(
            title=parser.title,
            author=parser.author,
            date=parser.date,
            content=parser.content,
            url=parser.url,
            tag=parser.tag,
            reviews=reviews
        )
    print('%s INDEXED' % parser.title)
    COUNTER[0][1] += 1


def douban_review_crawler(title):
    parser = DoubanParser()
    parser_pre = DoubanParserPre()
    url = 'https://www.douban.com/search'
    para = {'cat': 1001, 'q': title}
    response = requests.get(url, para)
    if response.status_code != 200:
        return None
    else:
        html = response.content.decode('utf-8')
        parser_pre.feed(html)
        if parser_pre.link == '':
            return None
        else:
            book_url = parser_pre.link
            response = keep_get(book_url)
            if response.status_code != 200:
                return None
            else:
                html = response.content.decode('utf-8')
                parser.feed(html)
                return parser.reviews


def duanwenxue_doc_crawler(index):
    parser = DuanwenxueParser()
    book_url = 'https://www.duanwenxue.com/article/%d.html' % index
    response = keep_get(book_url)
    if response.status_code != 200:
        return None
    else:
        html = response.content.decode('gb2312', 'ignore')
        parser.feed(html)
        parser.url = book_url
        match = clean_duanwenxue_doc(parser.content)
        if match:
            parser.content = match.group(1)
        else:
            return None

    filename = '%s.book' % os.path.join(DATA_DUANWENXUE_DIR, str(index))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(parser.content)
        print('BOOK[CN] %d SAVED' % index)
        COUNTER[1][0] += 1
    return parser


def duanwenxue_doc_crawler_(start, end):
    for index in range(start, end):
        duanwenxue_doc_crawler(index)


def duanwenxue_index_build(writer, parser):
    writer.add_document(
        title=parser.title,
        author=parser.author,
        date=parser.date,
        content=parser.content,
        url=parser.url,
        tag=parser.tag
    )
    print('%s INDEXED' % parser.title)
    COUNTER[1][1] += 1


def build_gutenberg(thread_num, doc_num):
    if os.path.exists(DATA_GUTENBERG_DIR):
        shutil.rmtree(DATA_GUTENBERG_DIR)
    if os.path.exists(INDEX_GUTENBERG_DIR):
        shutil.rmtree(INDEX_GUTENBERG_DIR)
    if os.path.exists(os.path.join(ROOT, 'bookbase.excpt')):
        os.remove(os.path.join(ROOT, 'bookbase.excpt'))

    os.makedirs(DATA_GUTENBERG_DIR)
    os.makedirs(INDEX_GUTENBERG_DIR)
    schema = GutenbergIndexSchema()
    create_in(INDEX_GUTENBERG_DIR, schema)

    writer = open_dir(INDEX_GUTENBERG_DIR).writer()
    for num in range(thread_num):
        pt = threading.Thread(target=gutenberg_doc_crawler_, args=(doc_num * num + 1, doc_num * (num + 1) + 1,))
        pt.start()
    time.sleep(5)
    while not GUTENBERG_PARSER_QUEUE.empty():
        it = threading.Thread(target=gutenberg_index_build, args=(writer, GUTENBERG_PARSER_QUEUE.get(),))
        it.start()
        it.join()
    writer.commit()


def build_duanwenxue(start, end):
    if os.path.exists(DATA_DUANWENXUE_DIR):
        shutil.rmtree(DATA_DUANWENXUE_DIR)
    if os.path.exists(INDEX_DUANWENXUE_DIR):
        shutil.rmtree(INDEX_DUANWENXUE_DIR)

    os.makedirs(DATA_DUANWENXUE_DIR)
    os.makedirs(INDEX_DUANWENXUE_DIR)
    schema = DuanwenxueIndexSchema()
    create_in(INDEX_DUANWENXUE_DIR, schema)

    writer = open_dir(INDEX_DUANWENXUE_DIR).writer()
    for index in range(start, end):
        parser = duanwenxue_doc_crawler(index)
        if parser:
            duanwenxue_index_build(writer, parser)
    writer.commit()


if __name__ == '__main__':
    # build(5, 3)
    # douban_review_crawler('Alice in Wonderland')
    build_gutenberg(50, 450)
    # build_duanwenxue(1, 22500)
    print(COUNTER)
