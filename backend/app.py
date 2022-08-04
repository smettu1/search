from flask import Flask, request
from flask_cors import CORS
from urllib.parse import unquote_plus
from pymongo import MongoClient
from celery.result import AsyncResult
from celery import uuid
import indexer
import celery_backend
import time 


app = Flask(__name__)
CORS(app)  # to allow the web application to access this app
appdb = MongoClient("mongodb://root:Secret@mongo").appdb
app.logger.info("initialized flask, CORS, and MongoClient")


@app.route("/task_status/<uuid:taskid>")
def task_status(taskid):
    time_val = time.time()
    app.logger.info("task_status for %s",taskid)
    result = AsyncResult(str(taskid))
    app.logger.info("task result for %s",result)
    return {"status": result.state,"result": result.get()}

@app.route("/upload_data")
def upload_articles():
    time_val = time.time()
    app.logger.info("upload_articles")
    # upload all the articles from the data directory into a new articles collection
    num = indexer.upload(appdb.articles, "data/top_500_lateral_wiki_utf8.csv")
    app.logger.info("upload_articles %s",time.time()-time_val)
    return {"count": num}

@app.route("/lookup/<string:article_id>")
def lookup(article_id):
    app.logger.info(f'lookup {article_id}')
    try:
        return appdb.articles.find({"_id": article_id}).next()
    except StopIteration:
        return {}

@app.route("/create_index")
def create_index_celery():
    time_val = time.time()
    app.logger.info("started create_index")
    # index all the documents in mongodb
    task_id = uuid()
    result = celery_backend.create_unigram.apply_async(task_id=task_id)
    unicnt, doccnt = 1,1#resp.get()
    app.logger.info("finished create_index %s",time.time()-time_val)
    return {"status": result.status,"result": result.result,"task_id": result.task_id}

@app.route("/search", methods=['GET'])
def search():
    searched_expression = request.args.get('q', "")
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))
    expr = unquote_plus(searched_expression)
    app.logger.info(f"search expr {expr} offset {offset} limit {limit} unigrams {appdb.unigrams}")
    results = indexer.search_unigrams(expr, offset, limit, appdb.unigrams)
    return {"results": [{"_id": res.docid, "title:": res.title, "score": res.score, "position": res.position} for res in results]}
