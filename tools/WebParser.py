from html.parser import HTMLParser
import re
import datetime
import requests


class GutenbergParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title          = ''
        self.tba            = ''    # $(Title) by $(Author)
        self.author         = 'Anonymous'
        self.date           = 'Unknown'
        self.content_url    = ''
        self.content        = ''
        self.url            = ''
        self.language       = ''
        self.tag            = ''

        self.meet_title     = False
        self.meet_tba       = False
        self.meet_date      = False
        self.meet_tag       = False

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if len(attrs) >= 2:
                if attrs[1] == ('type', 'text/plain') or attrs[1] == ('type', 'text/plain; charset=utf-8'):
                    self.content_url = attrs[0][1]
                if attrs[0] == ('class', 'block') and attrs[1][1][:15] == '/ebooks/subject':
                    self.meet_tag = True

        if tag == 'td':
            if len(attrs) >= 1:
                if attrs[0] == ('itemprop', 'headline'):
                    self.meet_title = True
                elif attrs[0] == ('itemprop', 'datePublished'):
                    self.meet_date = True

        if tag == 'h1':
            if len(attrs) >= 1:
                if attrs[0] == ('itemprop', 'name'):
                    self.meet_tba = True

        if tag == 'tr':
            if len(attrs) >= 4:
                if attrs[3][0] == 'content':
                    self.language = attrs[3][1]

    def handle_data(self, data):
        if self.meet_title:
            self.title = data.replace('\n', '').replace('\r', '')
            self.meet_title = False

            pattern_tba = re.compile('%s by (.*)' % self.title)
            match = pattern_tba.match(self.tba)
            if match and match.group(1) != '':
                self.author = match.group(1)

        if self.meet_tba:
            self.tba = data
            self.meet_tba = False

        if self.meet_date:
            self.date = data
            self.date_transfer()
            self.meet_date = False

        if self.meet_tag:
            self.tag += data
            self.tag = re.sub(r'[^A-Za-z]+', ' ', self.tag)
            self.tag = re.sub(r' and ', ' ', self.tag).split()[0]
            self.meet_tag = False

    def date_transfer(self):
        date_list = re.split(r'\W+|[年月日]', self.date)
        date_str = '%s %s %s' % tuple(date_list[:3])
        if len(date_list) == 3:     # Jun 25 2008
            date_struct = datetime.datetime.strptime(date_str, '%b %d %Y')
        else:                       # 2008 6 25
            date_struct = datetime.datetime.strptime(date_str, '%Y %m %d')
        self.date = date_struct
