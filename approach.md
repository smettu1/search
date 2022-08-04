


Issues:
    Ran into issue downloading the nltk stopwords corpus
        Used ubuntu docker image as alpine seems to have issue downloading with dns error 
        >>> import nltk
        >>> nltk.download('stopwords')
        [nltk_data] Error loading stopwords: <urlopen error [Errno -2] Name
        [nltk_data]     does not resolve>
        False
    Ran into SSL upstream error
        I believe its a upstream issue, for now not verifing the upstream source server

changed the code to run with flask + gevent library 
   >> Ideally flask is run to completion , patched inside request context to use gevents and run green threads 
      I did not see any significant improvement as pymongo needs to be async in nature which can be achieved by moving the 
      code to use motor and flask has to be re written either to gevent/tornado/async frameworks
        Flask
        2021-04-21:19:19:26,278 INFO     [app.py:58] finished create_index 63.03299403190613
        172.30.0.1 - - [21/Apr/2021 19:19:26] "GET /create_index HTTP/1.1" 200 -
        Gevent
        2021-04-21:19:20:46,850 INFO     [app.py:67] finished create_index 64.9284520149231
        172.30.0.1 - - [21/Apr/2021 19:20:46] "GET /create_index_gevent HTTP/1.1" 200 -
        Partly the problem is monkey patch did not work as expected.
        So i am abandoning this idea as if we have to make this work moving to native async lib is the best way 
        and writing the coroutines based arch will achieve better results instead of hacking flask req. processing 

Background worker method:
Flask is run to completion and ideally we should not do heavy compute in request context rather push to background 
distributed nodes so that more complex work can be done there and it helps client not time our or block on server.
Blow api i have split the job into multi phases one to do job in celery which generates task id
Second api to get response from the jobId
smettu@smettu-a01 search_engine % curl http://localhost:5001/create_index_celery
{
  "result": null,
  "status": "PENDING",
  "task_id": "eda330a1-8fe3-4848-a674-b3b3e0bfbb2e"
}
smettu@smettu-a01 search_engine % curl http://localhost:5001/task_status/eda330a1-8fe3-4848-a674-b3b3e0bfbb2e
{
  "result": [
    0,
    500
  ],
  "status": "SUCCESS"
}


1. As you will see [here](#not-perfect) the solution coded up in the backend implementation can be improved. You will see that it does not correctly implement TFIDF based search. This task is to try and fix that.
  - Look at `backend/indexer.py:search_unigrams(...)` this function is computing a score for each document and storing in `doc_scores`.
       ANS: ps.stem(x.lower()) for x in word_tokenize(content) if x.lower() not in stop_words
       I believe the comparision should be done on lowered value of token with stop_words else words like THE,The will escape and decrease the overall efficiency of algorithm.

       ANS: stop_words = set(stopwords.words("english") + list(punctuation))
       remove the puncations from the tokens as well.
             
  - Devise a better way to compute a score.

  - Describe your solution including your thought process and show some sample results. (You may also use the larger dataset in the next question for your examples).
    ANS: Currently we sum up every thing if one word has a lot of score it will be the first results 
          giving equal weight to every word wold help to solve that issue.

  - Note the wikipedia page for [TFIDF](https://en.wikipedia.org/wiki/Tf–idf) is a good starting point, but there is no correct answer.

2. Besides quality aspects the solution is also slow. On a [larger dataset](https://drive.google.com/file/d/1JBUtVTj_pUzlWVXmIwtmFYZdee-3JbYW/view) still with just 50k lines though, the indexing takes forever.
  - Look at `backend/indexer.py:create_unigram_index`. This extracts unigrams for each document and inserts it into a MongoDb collection called `unigrams`.

  - Devise an improvement to load this data faster. There is no need to change the underlying algorithm, but if that helps you are free to do so as well.
    ANS:
        Most of the task for the given data seems to be IO bound so moving the create/update to bulk operation saved almost half the time.
        I have not added the logic to deal with bulk exceptions , which needs to be handled by add single record and push the exception records into a Queue for manual intervention

  - Also note that this function raises a duplicate exception if called twice. As a bonus, devise a solution that addresses this problem also.
    ANS:
      API should and can be called multiple times, so instead of inserting record we need to search and see if the insert fails with duplicate error else we need to update data into mongo.
      This way inserts are very fast and updates will be through exception path
      We can do a bulk batched create or update operation to reduce app-db transaction time.

3. So far there is no constraint on which documents can or cannot be returned. We will change that now.
  - Introduce a new API endpoint which allows for expressions such as `transaction "code"`. Any word with the double quotes around it is taken as mandatory.
  - Your solution must enforce the following rules for an expression such as `foo "bar" baz "gaz"` all results must include `bar` and `gaz`and they should preferrably include `foo` and `baz`.
  - Devise an appropriate scoring rule and describe your solution with some examples.
  - Feel free to use a different syntax instead of quotes for mandatory terms
  - *Bonus*: implement a search with logical expressions such as `foo and (bar or baz) and not gaz`. In other words support `and`, `or`, and `not` operators using any syntax of your choice.