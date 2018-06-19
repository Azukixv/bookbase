from html.parser import HTMLParser
import re
import datetime
import requests
import time
import json


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


class GutenbergParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title = ''
        self.tba = ''  # $(Title) by $(Author)
        self.author = 'Anonymous'
        self.date = 'Unknown'
        self.content_url = ''
        self.content = ''
        self.url = ''
        self.language = ''
        self.tag = ''

        self.meet_title = False
        self.meet_tba = False
        self.meet_date = False
        self.meet_tag = False

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
        date_list = re.split(r'\W+|[年月日]', str(self.date))
        date_str = '%s %s %s' % tuple(date_list[:3])
        if len(date_list) == 3:  # Jun 25 2008
            date_struct = datetime.datetime.strptime(date_str, '%b %d %Y')
        else:  # 2008 6 25
            date_struct = datetime.datetime.strptime(date_str, '%Y %m %d')
        self.date = date_struct


class DoubanParserPre(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title = ''
        self.link = ''
        self.link_flag = False
        self.link_flag_count=0
        self.link_candi=''

    def handle_starttag(self, tag, attrs):
        if tag == 'input' and len(attrs)>=1:
            if attrs[0]==('placeholder',"搜索你感兴趣的内容和人"):
                self.title = re.sub('[^a-zA-Z0-9]',' ',str(attrs[5][1]))
                
        if tag == 'a':
            if str(attrs[0]).find('&pos=0') != -1:
                self.link = attrs[0][1]
                # print(self.link)
            if str(attrs[0]).find('&pos=') != -1 and self.link_flag_count==0:
                self.link_flag = True
                self.link_candi = attrs[0][1]

    def handle_data(self,data):
        if self.link_flag == True:
            self.link_flag = False
            stdata = re.sub('[^a-zA-Z0-9]',' ',str(data))
            # print('matching '+self.title+ ' in ' + stdata)
            if stdata.find(self.title) in range(0,5):
                self.link = self.link_candi
                self.link_flag_count = 1
                # print(self.link)


class DoubanParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title = ''
        self.meet_title = False
        self.r_title = ['', '', '']
        self.r_url = ['', '', '']
        self.r_title_count = 0
        self.r_title_count_flag = False
        self.r_brief = ['', '', '']
        self.r_b_count = 0
        self.r_b_count_flag = False
        self.r_full = ['', '', '']
        self.r_f_count = 0
        self.r_f_flag = False
        self.reviews = []

    def handle_starttag(self, tag, attrs):
        # get book title
        if tag == 'span':
            if len(attrs) >= 1:
                if attrs[0] == ('property', 'v:itemreviewed'):
                    self.meet_title = True

        # get review title
        if self.r_title_count < 3 and tag == 'a' and len(attrs) == 1:
            if str(attrs[0]).find('https://book.douban.com/review/') != -1:
                self.r_title_count += 1
                self.r_url[self.r_title_count - 1] = str(attrs[0])[
                                                     str(attrs[0]).find('https://book.douban.com/review/'):-2]
                self.r_title_count_flag = True

        # get brief review
        if self.r_b_count < 3 and tag == 'div' and len(attrs) >= 1:
            if attrs[0] == ('class', 'short-content'):
                self.r_b_count += 1
                self.r_b_count_flag = True

        # handleing full review
        if self.r_f_count < 3 and tag == 'div' and len(attrs) >= 3:
            if attrs[1] == ('class', 'review-short'):
                self.r_f_count += 1
                review_id = re.sub("\D", "", str(attrs[2]))
                url = 'https://book.douban.com/j/review/%s/full' % review_id
                response = keep_get(url)
                if response.status_code != 200:
                    return None
                else:
                    html = response.content.decode('utf-8')
                    jsonfile = json.loads(html)
                    self.r_full[self.r_f_count - 1] = jsonfile["html"]

    def handle_endtag(self, tag):
        if self.r_b_count_flag and tag == 'div':
            self.r_b_count_flag = False

        if tag == 'html':
            for i in range(0, 3):
                if self.r_title[i] != '':
                    self.reviews.append({'title': self.r_title[i],
                                         "brief": self.r_brief[i],
                                         "full": self.r_full[i],
                                         "url": self.r_url[i]})

    def handle_data(self, data):
        if self.meet_title:
            self.title = data
            self.meet_title = False

        if self.r_title_count_flag:
            self.r_title[self.r_title_count - 1] = data
            self.r_title_count_flag = False

        if self.r_b_count_flag:
            self.r_brief[self.r_b_count - 1] += data


class DuanwenxueParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title          = ''
        self.author         = 'Anonymous'
        self.date           = 'Unknown'
        self.content        = ''
        self.url            = ''
        self.tag            = ''

        self.meet_title     = False
        self.meet_author    = False
        self.meet_date      = False
        self.meet_content   = False
        self.num            = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if len(attrs) == 1:
                if attrs[0] == ('class', 'text'):
                    self.meet_date = True

        if tag == 'title':
            if len(attrs) == 0:
                self.meet_title = True

        if tag == 'div':
            if len(attrs) == 1:
                if attrs[0] == ('class', 'face'):
                    self.meet_author = True

        if tag == 'p':
            if len(attrs) == 0:
                self.meet_content = True

    def handle_endtag(self, tag):
        if tag == 'p':
            self.meet_content = False

    def handle_data(self, data):
        if self.meet_title:
            tmp = data.split('_')
            self.title = tmp[0]
            self.tag = tmp[1]
            self.meet_title = False

        if self.meet_author:
            self.num += 1
            if self.num == 2:
                data = re.sub(r'[\s\n\r]+', '', data)
                if data != '':
                    self.author = data
                self.meet_author = False
                self.num = 0

        if self.meet_content:
            self.content = self.content + data

        if self.meet_date:
            tmp1 = data
            self.date = re.search(r'\d*-\d*-\d*', tmp1).group()
            self.date_transfer()
            self.meet_date = False

    def date_transfer(self):
        date_struct = datetime.datetime.strptime(self.date, '%Y-%m-%d')
        self.date = date_struct
