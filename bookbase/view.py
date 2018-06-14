import os
import sys
sys.path.append('.')
sys.path.append('..')
from django.shortcuts import render
from whoosh.index import *
from whoosh.qparser import *
from whoosh.query import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_GUTENBERG_DIR = os.path.join(ROOT, 'index', 'gutenberg')

def index(request):
    return render(request, 'index.html')

def search(request):
    index = open_dir(INDEX_GUTENBERG_DIR)
    context = {}
    if request.POST:
        query_parser = QueryParser('content', index.schema)
        query = query_parser.parse(request.POST['q'])
        with index.searcher() as s:
            result = list(s.search(query))
            for i in range(len(result)):
                result[i] = dict(result[i])
            context['book_list'] = result
            context['q'] = request.POST['q']
    return render(request, 'index.html', context)