from whoosh.fields import *
from whoosh.analysis import *


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
