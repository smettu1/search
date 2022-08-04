import os
import time
from celery import Celery
from collections import Counter
from typing import List, Dict, Tuple

from string import punctuation
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
import redis
from index_interface import TermInDocument, SearchResult
from pymongo import MongoClient
import pickle    

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

import logging
import time
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)

@celery.task(name="create_unigram")
def create_unigram():
    """
    Create a unigram TF index from the aricle collection and store in unigram collection
    Returns the number of unigrams and documents
    """
    appdb = MongoClient("mongodb://root:Secret@mongo").appdb
    start_time = time.time()
    logging.info('Processing index request %s',time.time())
    stop_words = set(stopwords.words("english") + list(punctuation))
    ps = PorterStemmer()
    posting_list = {}
    r = redis.Redis("redis","6379")
    doccnt = 0
    for doc in appdb.articles.find():
        doccnt += 1
        content = doc["title"] + " " + doc["body"]
        word_tokens = [
            ps.stem(x.lower()) for x in word_tokenize(content) if x.lower() not in stop_words
        ]

        doclen = len(content)  # will be used to compute position feature
        wcount = 0
        for unigram in word_tokens:
            wcount += 1
            # process unigram
            if unigram not in posting_list:
                posting_list[unigram] = []
            if (len(posting_list[unigram]) == 0) or (posting_list[unigram][-1].docid != doc["_id"]):
                # first occurrence of word/unigram in document
                posting_list[unigram].append(
                    TermInDocument(doc["_id"], doc["title"], 1, float(doclen - wcount) / doclen, 0.0)
                )
            else:
                posting_list[unigram][-1].term_freq += 1
    logging.info('Done pre Processing index request %s',time.time()- start_time)
    # Now we have processed all docs
    # Compute the score for all documents of all unigrams
    # Sort all posting lists based on score.
    # weights to be learned
    unicnt = 0
    pickled_object = pickle.dumps(posting_list)
    r.set('posting_list', pickled_object)
    create_unigram_update.apply_async()
    logging.info('Done full Processing index request %s',time.time()- start_time)
    return (unicnt, doccnt)


@celery.task(name="create_unigram_update")
def create_unigram_update():
    appdb =  MongoClient("mongodb://root:Secret@mongo").appdb 
    r = redis.Redis("redis","6379")
    posting_list = pickle.loads(r.get('posting_list'))
    w_tf = 0.3
    w_pos = 0.7
    unicnt = 0
    bulk = appdb.unigram.initialize_unordered_bulk_op()
    counter = 0
    for unigram in posting_list:
        for doc in posting_list[unigram]:
            unicnt += 1
            doc.score = w_tf * doc.term_freq + w_pos * doc.position
        posting_list[unigram] = sorted(posting_list[unigram], key=lambda x: x.score, reverse=True)
        # Can optimize by doing bulk insert
        record ={
                    "_id": unigram,
                    "docs": [
                        {
                            "docid": doc.docid,
                            "title": doc.title,
                            "term_freq": doc.term_freq,
                            "position": doc.position,
                            "score": doc.score,
                        }
                        for doc in posting_list[unigram]
                    ],
                }
        counter += 1
        try:
            appdb.unigrams.insert_one(record)
        except DuplicateKeyError:
            bulk.find({"_id": unigram}).update({"$set":record})
            if (counter % 500 == 0):
                bulk.execute()
                bulk = appdb.unigram.initialize_unordered_bulk_op()
        except Exception as e:
            logging.error("Error updating record",e)
    bulk.execute()
    logging.info('Done full Processing save request ')