## How to run
Make sure you have docker and docker-compose installed on your machine. Then run the following command:
```
docker-compose up
```

## How to stop
```
docker-compose down
```

## How to run tests
Since we have two services, we need to run tests for each service separately. To run tests for API service, run the following command:
```
cd endpoints && python -m unittest discover
```

## What does the api do?
It actually has docs, just go to localhost:5000/docs to see the docs.


## Design choices and assumptions

### Why splitting the application into two services?
By splitting into two services, we can achieve two things:
1. We can scale the two services independently. For example, if we have a lot of requests for the API, we can scale the API service without scaling the database service.
2. When one service fails the other service can still work. For example, if github injector fails, the user can still use the API to get the data from the database.
When API fails, the github injector can still insert data into the queue, which will be picked up by the API when it is back online.

### Why using Kafka?
Frankly, it's the first queue that comes to my mind which has pub/sub, while allowing to retrieve old messages (not like Reddis).

### Why using sqlite?
Really simple to use and good enough for our purpose. We can easily switch to another database if needed since we use SQLAlchemy ORM.

### Github injectors specifics
The gh API provides us with multiple pages of the latest events. We thus try to walk over the pages until we reach the event with the id we already have already seen. Note that this can create duplicates. since the event pages are ever-moving. We also make sure that we don't query more often than gh api recommends. Lastly, we employ the etag mechanism to avoid querying the same page twice.

### How are data persisted?
We use a named volume to persist the data in docker.


## Code diagram
### Github injector
![GH Injector](img/injector.png)

### API
![API](img/api.png)
