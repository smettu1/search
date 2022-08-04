# Search Engine

In this exercise you are provided the basic scaffolding of a search engine. Please run the [setup](#setup) steps. You are also provided a basic search backend implementation that you can run in [basic backend steps](#load-data-and-create-a-unigram-index).
Then onwards you can focus on improving the solution in a number of ways depending on your area of chosen expertise. Please pick from _**one**_ of 
- Software Developer - Frontend
- Software Developer - Backend
- Software Developer - AI/ML

Please provide your working code solution including a file `approach.md` describing your method. Create a zip file of the folder and send it to us. Also, please appropriately document and format your code out of consideration for the readers!

## Software Developer - Frontend

We have 3 frontend applications in the frontend folder, ReactJS, VueJS and pure JS application. You can choose any one of them for the implementation of the question. These applications are available from your localhost on ports 3000, 8080, and 3001 respectively.

Implement a search results page as given in the wireframe `wireframe.png`.
<img src="wireframe.png" alt="wireframe" width="200"/>

The list of features that should be supported:

1. Implement basic search results (Title & ID)
2. Implement full search results (Title, ID & Desc)
3. Implement dialog box to show full description on click of any search result (Ref `wireframe_detailed.png`)<img src="wireframe_detailed.png" alt="wireframe_detailed" width="200"/>
4. Implement a responsive page
5. Implement infinite pagination
6. Highlight the search terms in the search results as shown in the wireframe
7. Improve the peformance of the search results
8. Implement client side filtering for position and score (eg: score between 1 to 2 and postion above 0.95)

### APIs

#### Search

```
curl http://localhost:5000/search?q=<search_term>&offset=<offset>&limit=<limit>

```

###### Search Example

```
curl http://localhost:5000/search?q=transaction+code&offset=0&limit=10

```

#### Detailed Information

```
curl http://localhost:5000/lookup/<_id>

```

###### Detailed Information Example

```
curl http://localhost:5000/lookup/wikipedia-20968452

```

## Software Developer - Backend

1. As you will see [here](#not-perfect) the solution coded up in the backend implementation can be improved. You will see that it does not correctly implement TFIDF based search. This task is to try and fix that.
  - Look at `backend/indexer.py:search_unigrams(...)` this function is computing a score for each document and storing in `doc_scores`.
  - Devise a better way to compute a score.
  - Describe your solution including your thought process and show some sample results. (You may also use the larger dataset in the next question for your examples).
  - Note the wikipedia page for [TFIDF](https://en.wikipedia.org/wiki/Tf–idf) is a good starting point, but there is no correct answer.
2. Besides quality aspects the solution is also slow. On a [larger dataset](https://drive.google.com/file/d/1JBUtVTj_pUzlWVXmIwtmFYZdee-3JbYW/view) still with just 50k lines though, the indexing takes forever.
  - Look at `backend/indexer.py:create_unigram_index`. This extracts unigrams for each document and inserts it into a MongoDb collection called `unigrams`.
  - Devise an improvement to load this data faster. There is no need to change the underlying algorithm, but if that helps you are free to do so as well.
  - Also note that this function raises a duplicate exception if called twice. As a bonus, devise a solution that addresses this problem also.
3. So far there is no constraint on which documents can or cannot be returned. We will change that now.
  - Introduce a new API endpoint which allows for expressions such as `transaction "code"`. Any word with the double quotes around it is taken as mandatory.
  - Your solution must enforce the following rules for an expression such as `foo "bar" baz "gaz"` all results must include `bar` and `gaz`and they should preferrably include `foo` and `baz`.
  - Devise an appropriate scoring rule and describe your solution with some examples.
  - Feel free to use a different syntax instead of quotes for mandatory terms
  - *Bonus*: implement a search with logical expressions such as `foo and (bar or baz) and not gaz`. In other words support `and`, `or`, and `not` operators using any syntax of your choice.

## Software Developer - AI/ML

The exercise here is to build semantic search, i.e. embedding based search.

1. Baseline semantic search:
   1. Download the [larger dataset of 50k documents](https://drive.google.com/file/d/1JBUtVTj_pUzlWVXmIwtmFYZdee-3JbYW/view)
   2. The goal is to build a embedding for these documents and an embedding generator for search expressions.
   3. Then you will need to store the document embeddings in a place where you can retrieve them.
   4. At serving time, given a search text, which could be a single word, you will need to generate an embedding for the search text.
   5. You will need to find documents with embeddings that have the highest dot-product with the embedding of search test. This is also called Maximum Iner Product Search. if the embeddings you have generated are l2-normalized, then this is same as nearest neighbor search among the document embeddings.
2. Further optimzation of serving time latency:
   1. Initially you can use Mongodb / Redis cache as way to store any embeddings you need to generate.
   2. To make serving faster, consider using optimized implementations of Maximum Inner Product Search. Some implementations that could come in handy are:
      1. [Scann](https://github.com/google-research/google-research/tree/master/scann), [example notebook](https://github.com/google-research/google-research/blob/master/scann/docs/example.ipynb)
      2. [NMS Lib](https://github.com/nmslib), [example notebook](https://nbviewer.jupyter.org/github/nmslib/nmslib/blob/master/python_bindings/notebooks/search_vector_dense_optim.ipynb)

The proposal above is a special case of [StarSpace](https://github.com/facebookresearch/StarSpace). A key aspect you will need to figure out here is how to mine search expressions from the input document set. Remember you are not given actual search terms that people might use. You have just been given documents, and you have to come up with a generator for the search expression from the documents.

## Software Developer - Full stack

1. Besides some combination of ideas above, you could look into implementing auto-complete ([Ref link](https://medium.com/@prefixyteam/how-we-built-prefixy-a-scalable-prefix-search-service-for-powering-autocomplete-c20f98e2eff1)) as well.


## Evaluation

We will prefer working solutions. We will also read your `Approach.md` file.

## Setup

To get started you will first need to install [Docker desktop](https://www.docker.com/products/docker-desktop). This works well on Ubuntu and Mac laptops. However, on Windows you might need a Linux VM if you encounter issues.

Next build the development environment as follows (this will take a minute or so):

    docker-compose build

Now, you can bring up docker containers in the background:

    docker-compose up -d

You should be able to list the running containers:

    docker ps

```
CONTAINER ID   IMAGE                COMMAND                  CREATED          STATUS          PORTS                    NAMES
1aad73daea98   search_engine_vue-app       "docker-entrypoint.s…"   9 seconds ago    Up 7 seconds    0.0.0.0:8080->8080/tcp   search_engine_vue-app_1
c05e73470944   search_engine_pure-js-app   "docker-entrypoint.s…"   6 minutes ago    Up 6 minutes    0.0.0.0:3001->3001/tcp   search_engine_pure-js-app_1
054f4268e9ce   search_engine_react-app     "docker-entrypoint.s…"   7 minutes ago    Up 6 minutes    0.0.0.0:3000->3000/tcp   search_engine_react-app_1
853c1aad2182   search_engine_backend       "flask run --host=0.…"   7 minutes ago    Up 7 minutes    0.0.0.0:5000->5000/tcp   search_engine_backend_1
71168dcc173d   mongo:latest                "docker-entrypoint.s…"   17 minutes ago   Up 17 minutes   27017/tcp                search_engine_mongo_1
09e063692b02   redis:latest                "docker-entrypoint.s…"   17 minutes ago   Up 17 minutes   6379/tcp                 search_engine_redis_1
```

If needed you can directly connect to one of the containers:

    docker exec -it <container name> sh

However, we will primarily interact with the containers through the web interface or through the `curl` command line tool. Note that any changes that you make to the source code in the backend or the frontend directories will automatically show up in the container.

## Load data and create a unigram index

First we will load all the wikipedia articles in the file `backend/data/top_500_lateral_wiki_utf8.csv` into the mongodb collection called `articles` using the `upload_data` API endpoint.

    curl http://0.0.0.0:5000/upload_data

```
{
  "count": 500
}
```

The code for the backend is in the `/backend/indexer.py` file and the API endpoints are defined in `/backend/app.py`. Any changes made to those files are immediately reflected in the API.

Verify that you can now view a single document using its identifier with the `lookup` endpoint.

    curl http://0.0.0.0:5000/lookup/wikipedia-20968452

```
{
  "_id": "wikipedia-20968452",
  "body": "A transaction code (or t-code) consists of letters, numbers, or both, and is entered in the command field. Each function in SAP ERP has an SAP transaction code associated with it.  Use. A t-code is used to access functions in a SAP application more rapidly. By entering a t-code instead of using the menu, navigation and execution are combined into a single step, much like shortcuts in the Windows OS.",
  "title": "T-code"
}
```

Now we can create an index of unigrams (this will take a few minutes).

    curl http://localhost:5000/create_index

```
{
  "document count": 500,
  "unigram count": 32098
}
```

And search for an expression such as "transaction code"

    curl "http://0.0.0.0:5000/search?q=transaction+code&offset=0&limit=10"

```
{
  "results": [
      {
          "_id": "wikipedia-2701077",
          "position": 0.9955646537018082,
          "score": 5.796895257591265,
          "title:": "Dynamic-link library"
      },
      {
          "_id": "wikipedia-1882576",
          "position": 0.997563946406821,
          "score": 3.9982947624847744,
          "title:": "Area code 321"
      },
      {
          "_id": "wikipedia-10933",
          "position": 0.9976649623575828,
          "score": 3.0983654736503077,
          "title:": "Functional programming"
      },
      {
          "_id": "wikipedia-19321330",
          "position": 0.90254730713246,
          "score": 3.031783114992722,
          "title:": "Nightclub"
      },
      {
          "_id": "wikipedia-30007",
          "position": 0.982784135753749,
          "score": 2.7879488950276246,
          "title:": "The Matrix"
      },
      {
          "_id": "wikipedia-20968452",
          "position": 0.9902200488997555,
          "score": 2.5880195599022002,
          "title:": "T-code"
      },
      {
          "_id": "wikipedia-7202313",
          "position": 0.9974842767295597,
          "score": 2.4982389937106917,
          "title:": "Electrical code"
      },
      {
          "_id": "wikipedia-8149918",
          "position": 0.9799865981684164,
          "score": 2.4859906187178913,
          "title:": "Economy of Kosovo"
      },
      {
          "_id": "wikipedia-200315",
          "position": 0.8923716012084593,
          "score": 1.9106873111782479,
          "title:": "Marie-Joseph Angélique"
      },
      {
          "_id": "wikipedia-660591",
          "position": 0.9710008678044547,
          "score": 1.8797006074631182,
          "title:": "Non-tariff barriers to trade"
      }
  ]
}
```

### Not Perfect

Note that the best answer `wikipedia-20968452` is showing up in the 6th position for this search string. We will want to fix this!

## Notes about docker

### Additional packages

If you need to install additional packages in the backend container you should edit the `requirements.txt` file and rebuild and restart docker compose. You may also login to the backend container as follows and manually directly install the packages, but note that these changes will not be persisted if you rebuild.

    docker exec -ti search_engine_backend_1 sh
    pip install <package name>

### Logging output

Any output printed in the docker containers can be viewed in the docker container logs. For example, the following will show the logs for the backend container,

    docker logs search_engine_backend_1

Note that you need to flush the output for it to be visible. The `backend/app.py` has some examples of using `app.logger.info` to generate logging, which doesn't need to be explicitly flushed.

## Cleanup

    docker-compose rm --force --stop

# References

- [PyMongo](https://www.w3schools.com/python/python_mongodb_getstarted.asp)
- [Prefixy](https://medium.com/@prefixyteam/how-we-built-prefixy-a-scalable-prefix-search-service-for-powering-autocomplete-c20f98e2eff1)
- [tf-idf](https://en.wikipedia.org/wiki/Tf–idf)
