# coding: utf-8
import json
import sys

import pickle
import pymysql.cursors
import os
from nltk import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
from nltk.stem.porter import *
import hashlib
import urllib
import json
import time
import math
import os.path

import sys


NUM_OF_ARTICLES = 5330933

# Database connection information
DATABASE_HOST = 'localhost'
DATABASE_USER = 'root'
DATABASE_PASS = 'password'
DATABASE_DB = 'wikipedia'


def mysql_connection():
    """
    Creates a MySQL database connection
    """
    return pymysql.connect(host=DATABASE_HOST,
                           user=DATABASE_USER,
                           password=DATABASE_PASS,
                           db=DATABASE_DB,
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.SSCursor)

def fetch_pageids(start=0):

    connection = mysql_connection()

    n_aricles = NUM_OF_ARTICLES
    limit = 20

    end = math.ceil(n_aricles / limit)

    start_time = time.time()
    last_print_time = time.time()

    try:
        with connection.cursor() as cursor:

            for i in range(start, end):

                if not os.path.isfile("out/%d.json" % i):

                    offset = i * limit

                    # Read records
                    cursor.execute("SELECT page_id FROM page WHERE page_is_redirect = 0 AND page_namespace = 0 ORDER BY page_id LIMIT %d OFFSET %d" % (limit, offset))

                    query_result = [str(r) for (r,) in cursor.fetchall()]

                    pageids = '|'.join(query_result)

                    headers = {'User-Agent': 'Wikipedia-Summary-Dataset (machine learning research) http://thijs.ai/Wikipedia-Summary-Dataset/'}
                    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?format=json&maxlag=5&action=query&prop=extracts&exintro=&explaintext=&pageids=%s" % pageids, None, headers)
                    json_result = urllib.request.urlopen(req).read()
                    data = json.loads(json_result)

                    if "batchcomplete" in data and "warnings" not in data:
                        file = open("out/%d.json" % i, "wb")
                        file.write(json_result)
                        file.close()
                    else:
                        if "warnings" in data:
                            print("%d failed: %s" % (i, json.dumps(data["warnings"])))
                        else:
                            print("%d failed" % i)

                    cur_time = time.time()

                    if cur_time - last_print_time > 1:
                        last_print_time = cur_time

                        duration = cur_time - start_time
                        duration_per_item = duration / (((i - start) * limit) + 1)
                        items_per_second = 1 / duration_per_item

                        articles_left = n_aricles - offset

                        eta = articles_left * duration_per_item / 60

                        print("%d: %d/%d   %.0f p/s   %.0f minutes left" % (i, offset, n_aricles, items_per_second, eta))

    finally:
        connection.close()

if __name__ == '__main__':

    if len(sys.argv) == 2:
        fetch_pageids(int(sys.argv[1]))
    else:
        fetch_pageids()