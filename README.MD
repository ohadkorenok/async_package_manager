# Package Manager:

## Project structure:
The API is written in FastAPI, Redis and MongoDB.
FastAPI is used in order to use asyncio as its best, since I/O is our bottleneck. 

For caching, we use Redis backend.

Our storage server is MongoDB

We have worker/s that will update our database every constant time (configurable)


In order to run the system , just run : 

`docker-compose up -d`.

And the server will be visible in http://localhost:8008/ 

For easy reference, you can use also SwaggerUI: 
http://localhost:8008/docs#/


For running the system with multiple workers:

`docker-compose up -d --scale scheduler=n where n is number of workers`

In order to run tests, please enter to the nodes of the desired container using 

`docker ps`

`docker exec it <container_id> bash`

`pytest`

Have fun! 