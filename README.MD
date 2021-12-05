# Package Manager: The task: 

### Background

NodeJS has a managed packages environment called npm. A package is a functional NodeJS module with versioning, documentation, dependencies (in the form of other packages), and more. npm is being constantly updated with new packages and new versions of existing packages.

In order to identify vulnerabilities in certain packages, the following (rough) process takes place:

  1. User provides name of package for analysis
  2. We fetch the overall set of dependencies of given package
  3. We compare the set of dependencies with a managed set of vulnerable packages
  4. We identify remediation paths (upgrades and/or patches for vulnerable packages)
  5. Users choose their preferred remediation action and we apply it

### Exercise

In this exercise we will focus on on stages 1 and 2 for a package that is already published on npmjs.com

Your task is to design and implement a web service that, given a name of an npm package, returns its dependent packages to be used by the consequent stage (3).

You can obtain package data through the npm registry: `https://registry.npmjs.org/<package_name>/<version_or_tag>`. For example: https://registry.npmjs.org/express/latest or https://registry.npmjs.org/async/2.0.1

#### Things to consider

  1. Look at the inner "dependencies" object for analysis of first-order dependencies.
  2. There are currently over 800K packages on npmjs.com, and the number is growing all the time.
  3. The packages update from time to time, just as their dependencies.
  4. What makes a good web service? API, architecture, data storage, low latency, scalability, monitoring, you name it :)
  5. Consider the quality and structure of your codebase; is it maintainable?
  6. Consider production readiness (to some extent) and is it safe to deploy changes?

#### Implementation

  1. A working web application that, given a name of an npm published package, returns the set of dependencies for said package.
  2. Present the dependencies in a tree view.
  3. Account of asyncronous fetching of dependencies as you see fit.
  4. Cache relevant data so that repeated requests resolve with minimum latency.
  
  **We strongly suggest to implement this task in Python, as this is the main language used by our team**

Good luck!

----------------------


## Project structure:

The API is written in FastAPI, Redis and MongoDB. FastAPI is used in order to use asyncio as its best, since I/O is our
bottleneck.

For caching, we use Redis backend.

Our storage server is MongoDB

We have worker/s that will update our database every constant time (configurable)

## Run

In order to run the system , just run :

`docker-compose build`

`docker-compose up -d`.

And the server will be visible in http://localhost:8008/

For easy reference, you can use also SwaggerUI:
http://localhost:8008/docs#/

For running the system with multiple workers:

`docker-compose up -d --scale scheduler=n where n is number of workers`

## Run tests

In order to run tests, please enter to the nodes of the desired container using

`docker ps`

`docker exec it <container_id> bash`

`pytest`

## Logs

logs will be written in each container. One for worker and one for server. You can read them from within the container

Have fun! 