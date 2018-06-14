# bookbase
A simple book search system

## Dependencies
We require python >= 3.5 and Django >= 2.0. To install all the dependencies, use

`pip3 install -r requirements.txt`

If you have installed the conda, use

`conda install --file requirements.txt`

## Preparation
In order to search the book, you need to first run the `build.py`, which will crawl books info from the Internet and build index for those books.

## Start Searching
Use

`python3 manage.py runserver`

to start the web service. Visit `127.0.0.1:8000` to see the result.
