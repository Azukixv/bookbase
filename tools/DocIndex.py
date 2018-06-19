from whoosh.fields import *
from whoosh.analysis import *
from jieba.analyse import ChineseAnalyzer


class GutenbergIndexSchema(SchemaClass):
    title = TEXT(
        analyzer=StemmingAnalyzer(),
        stored=True,
        field_boost=2.0,
        spelling=True,
        sortable=True,
        vector=True
    )
    author = TEXT(
        stored=True,
        spelling=True,
        sortable=True
    )
    date = DATETIME(
        stored=True,
        sortable=True
    )
    content = TEXT(
        analyzer=StemmingAnalyzer(),
        spelling=True,
        vector=True
    )
    url = STORED()
    tag = KEYWORD(
        stored=True
    )
    reviews = STORED()


class DuanwenxueIndexSchema(SchemaClass):
    title = TEXT(
        analyzer=ChineseAnalyzer(),
        stored=True,
        field_boost=2.0,
        sortable=True,
        vector=True
    )
    author = TEXT(
        stored=True,
        sortable=True
    )
    date = DATETIME(
        stored=True,
        sortable=True
    )
    content = TEXT(
        analyzer=ChineseAnalyzer(),
        vector=True
    )
    url = STORED()
    tag = KEYWORD(
        stored=True
    )
