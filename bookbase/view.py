import os
import sys
from typing import Dict, List, Any, Union

from whoosh.searching import ResultsPage

sys.path.append('.')
sys.path.append('..')
import datetime
from django.shortcuts import render
from whoosh import scoring
from whoosh.index import *
from whoosh.qparser import *
from whoosh.query import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_GUTENBERG_DIR = os.path.join(ROOT, 'index', 'gutenberg')
INDEX_DUANWENXUE_DIR = os.path.join(ROOT, 'index', 'duanwenxue')


def index(request):
    return render(request, 'index.html')


def search(request):
    context = {}
    if request.POST:
        if request.POST['lan'] == 'en':
            index = open_dir(INDEX_GUTENBERG_DIR)
            query_parser = QueryParser(request.POST['field'], index.schema)
            query = query_parser.parse(request.POST['q'])
        else:
            index = open_dir(INDEX_DUANWENXUE_DIR)
            query_parser = QueryParser(request.POST['field'], index.schema)
            query = query_parser.parse(request.POST['q'])

        with index.searcher(weighting=scoring.BM25F()) as s:
            book_list = list(s.search_page(query, 1, pagelen=15))

            for i in range(len(book_list)):
                book_list[i] = dict(book_list[i])
                # book_list = sorted(book_list, key=lambda book:book['title'])
            for book in book_list:
                book['date'] = book['date'].strftime('%b %d, %Y')
            context['book_list'] = book_list
    return render(request, 'index.html', context)
