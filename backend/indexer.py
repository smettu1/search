"""
indexer exposes a function inex_docs which if given a data file, 
processes every line of that file, builds an inverted index from unigrams to a list of Document objects.
"""

from collections import Counter
from typing import List, Dict, Tuple

from string import punctuation
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from index_interface import TermInDocument, SearchResult

#debug
import logging
import time
import heapq
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)
ADD = 1
OR = 2
DEL = 3

def get_title_and_body(content: str) -> Tuple[str, str]:
    title, body = content.split("  ", 1)
    # remove leading quote in title
    if title[0] == '"':
        title = title[1:].lstrip()
    # remove trailing quote in body
    if body[-1] == '"':
        body = body[:-1].rstrip()
    # restrict title to at most 10 words
    if len(title) > 10:
        title = " ".join(title.split(" ")[:10])
    return title, body

def upload(collection: Collection, filename: str) -> int:
    # uploads articles from file into the mongodb collection and returns a count
    with open(filename) as fp:
        cnt = 0
        # TODO if the line length is too big this may crash the process
        # read fixed size buffer and parse for new line
        for line in fp:
            if len(line) == 0:
                continue
            fields = line.split(",", 1)
            docid = fields[0].strip()
            content = fields[1].strip()
            title, body = get_title_and_body(content)
            document = {"_id": docid, "title": title, "body": body}
            try:
                collection.insert_one(document)
            except DuplicateKeyError:
                collection.update_one({"_id": docid}, {"$set": {"title": title, "body": body}})
            cnt += 1
    return cnt

# Processing:
# 1. Find unigrams in content.
# 2. Remove stop words
# 3. Compute the position fraction of each unigram in the document. This is 1 if the it is the
# first word and close to 0 if it is the last word.
# 4. Compute the frequency of each unigram in the document
# 5. For each every unigram maintain a list of documents that the unigram can be found in.
# 5b. In addition to the docid, keep other metadata like the frequency of the unigram in
#     the document, the position of the unigram in the document.
def create_unigram_index(articles: Collection, unigrams: Collection) -> Tuple[int, int]:
    """
    Create a unigram TF index from the aricle collection and store in unigram collection
    Returns the number of unigrams and documents
    """
    start_time = time.time()
    logging.info('Processing index request %s',time.time())
    stop_words = set(stopwords.words("english") + list(punctuation))
    ps = PorterStemmer()
    posting_list = {}
    doccnt = 0
    for doc in articles.find():
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
    w_tf = 0.3
    w_pos = 0.7
    unicnt = 0
    for unigram in posting_list:
        unicnt += 1
        for doc in posting_list[unigram]:
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
        try:
            unigrams.insert_one(record)
        except DuplicateKeyError:
            unigrams.update_one({"_id": unigram}, {"$set":record})
        except Exception as e:
            logggin.error("Error updating record",e)
    logging.info('Done full Processing index request %s',time.time()-start_time)
    return (unicnt, doccnt)

def search_unigrams(expr: str, offset: int, limit: int, unigrams: Collection) -> List[SearchResult]:
    stop_words = set(stopwords.words("english") + list(punctuation))
    ps = PorterStemmer()
    tokens = []
    # in case if there are special chars parse the tokens 
    if '!' in expr or '$' in expr or '|' in expr:
        search_words =  parse_tokens(expr)
    else:
        # Convert to lowercase and also stem the words
        search_words = [ps.stem(x.lower()) for x in word_tokenize(expr)]
        # Remove stop words from the set of words to search
        search_words = [x for x in search_words if x not in stop_words]
        search_words = [(1,x) for x in search_words]
    logging.info(' full resp %s %s %s',search_words,word_tokenize(expr),expr)
    # Add the score for each unigram
    doc_scores = Counter()
    doc_scores_new = Counter()
    doc_dict = {}
    docid_to_title = {}
    docid_to_position = {}
    for prio,word in search_words:
        result = unigrams.find_one({"_id": word})
        if result is not None:
            for doc in result["docs"]:
                # if the operation is NOT delete the docs from the response
                if prio == DEL:
                    if doc["docid"] in doc_dict.keys():
                        doc_dict.pop(doc["docid"])
                    continue
                # Score of a document is the sum of scores of the document over all searched terms  
                if doc["docid"] in doc_dict.keys():
                    if word in doc_dict[doc["docid"]].keys():
                        doc_dict[doc["docid"]][word] += doc["score"]
                    else:
                        doc_dict[doc["docid"]][word] = doc["score"]
                else:
                    doc_dict[doc["docid"]] = {}
                    doc_dict[doc["docid"]][word] = doc["score"]
                doc_scores[doc["docid"]] += doc["score"]
                docid_to_title[doc["docid"]] = doc["title"]
                docid_to_position[doc["docid"]] = doc["position"]
    # Give equal priority to all the words to normalize the search
    for k,v in doc_dict.items():
        temp = 0
        for k1,v1 in v.items():
            temp += v1
        doc_scores_new[k] +=(temp/len(search_words))
    final_results = [SearchResult(docid, docid_to_title[docid], score, docid_to_position[docid],) for docid, score in doc_scores_new.most_common(offset+limit)]
    return final_results[offset:offset+limit]

def parse_tokens(tokens: string)->Dict[List]:
    token_dict = {'AND':set(),'OR':set(),'NOT':set()}
    last_str,cur_str = "",""
    last_tok,cur_tok = "",""
    ps = PorterStemmer()
    resp = []
    stop_words = set(stopwords.words("english") + list(punctuation))
    for i in tokens:
        if i in ["|","$",'!']:
            if i == '|':
                cur_tok = '|'
            elif i == '$':
                cur_tok = '$'
            elif i == '!':
                cur_tok = '!'
            # handle the case where its the first token
            if last_tok == "":
                last_str,cur_str = cur_str,""
                last_tok,cur_tok = cur_tok,""
                continue
            # else update the token dict with the tokes
            else:
                last_str,cur_str = ps.stem(last_str.lower()),ps.stem(cur_str.lower())
                if last_tok == '$':
                    token_dict['AND'].add(last_str)
                    token_dict['AND'].add(cur_str)
                elif last_tok == '|':
                    token_dict['OR'].add(cur_str)
                elif last_tok == '!':
                    token_dict['NOT'].add(cur_str)
                last_str,cur_str = cur_str,""
                last_tok,cur_tok = cur_tok,""
        else:
            cur_str += i
    if cur_str:
        if last_tok == '$':
            token_dict['AND'].add(cur_str)
        elif last_tok == '|':
            token_dict['OR'].add(cur_str)
        elif last_tok == '!':
            token_dict['NOT'].add(cur_str)
    # Assign first priority to AND and second to OR third priority to NOT
    [heapq.heappush(resp,(AND,x)) for x in token_dict['AND'] if x not in stop_words]
    [heapq.heappush(resp,(OR,x)) for x in token_dict['OR'] if x not in stop_words]
    [heapq.heappush(resp,(DEL,x)) for x in token_dict['NOT'] if x not in stop_words]
    return resp