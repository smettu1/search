# Search Engine
Search implementation using tfidf index. 

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
