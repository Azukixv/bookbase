# coding=utf-8
import os
import threading
import time
import requests
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))

class GutenbergParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text_url = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if len(attrs) >= 2 and (attrs[1] == ('type', 'text/plain') or attrs[1] == ('type', 'text/plain; charset=utf-8')):
                self.text_url = attrs[0][1]

def tokenizing(text):
    text = text.lower()
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('  ', ' ')
    return text

def keep_get(url):
    keep_alive = True
    while keep_alive:
        try:
            result = requests.get(url)
            keep_alive = False
        except Exception as e:
            print('LINK REESTABLISHMENT')
            time.sleep(1)
    return result

def get_text_from_gutenberg(start, end):
    parser = GutenbergParser()

    for index in range(start, end):
        print('BOOK INDEX:\t%d' % index)
        book_url = 'http://www.gutenberg.org/ebooks/' + str(index)
        # print('BOOK URL:\t%s' % book_url)
        response = keep_get(book_url)
        if response.status_code != 200:
            continue
        else:
            # print('200 OK')
            html = response.content.decode('utf-8')
            parser.feed(html)
            if parser.text_url != '':
                if parser.text_url[0:4] != 'http':
                   parser.text_url = 'http:' + parser.text_url
                try:
                    text = keep_get(parser.text_url)
                    text = text.content.decode('utf-8-sig', 'ignore')
                    text = tokenizing(text)
                except Exception as e:
                    with open('bookbase.excpt', 'a', encoding='utf-8') as et:
                        log = '[Gutenberg] %s:\t%s\n' % (str(index), str(e))
                        et.write(log)
                    continue
            else:
                with open('bookbase.excpt', 'a', encoding='utf-8') as et:
                        log = '[Gutenberg]:\tdid not get text url from http://www.gutenberg.org/ebooks/%d\n' % index
                        et.write(log)
                continue

            filename = '%s\\data\\gutenberg\\%s.book' % (ROOT, str(index))
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
                print('BOOK %d SAVED' % (index))

        time.sleep(5)


if __name__ == '__main__':

    os.makedirs(ROOT + '\\data\\gutenberg')
    with open('bookbase.excpt', 'w', encoding='utf-8'):
        pass

    for i in range(20):
        t = threading.Thread(target=get_text_from_gutenberg, args=(200*i+1, 200*i+401, ))
        t.start()