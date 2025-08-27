# This is the repository for setting up BPL

## The stack

### Postgresql

Nothing fancy. Only accessed by the backend.
Any other queries by other services (for example the discord bot) must go through the backend via REST call

### Kafka

For now only used to cache client queries from the backend to replay at a later point in time.

### Loki / Grafana / Prometheus

For logging / metrics and visualizations. Exposed under /monitoring

### Nginx

Reverse proxy to route requests to the services.

- /api/\* -> backend
- /monitoring/\* -> grafana
- /watchtower -> watchtower
- anything elese -> frontend

### Watchtower

Downloads and deploys new images from dockerhub when triggered via webhook from github actions

### Backend

https://github.com/BPL-v2/bpl-2-backend

### Discord Bot

https://github.com/BPL-v2/bpl-2-discord-bot

### Frontend

https://github.com/BPL-v2/bpl-2-fronend



## Environment variables

We use a .env file for out environment variables.

run

```sh
echo "# postgres / backend
DATABASE_HOST=localhost                                 # basic postgres stuff
DATABASE_PORT=5432                                      # basic postgres stuff
POSTGRES_USER=postgres                                  # basic postgres stuff
POSTGRES_PASSWORD=postgres                              # basic postgres stuff
DATABASE_NAME=postgres                                  # basic postgres stuff

# discord bot / backend
DISCORD_BOT_TOKEN=dummy                                 # to sign in the discord bot both to discord and to the backend

# discord bot
BACKEND_URL_FOR_DISCORD_BOT=http://localhost:8000/api   # used for making requests to the backend (internally over docker network)

# backend
POE_CLIENT_ID=dummy                                     # poe oauth
POE_CLIENT_SECRET=dummy                                 # poe oauth
POE_CLIENT_TOKEN=dummy                                  # used for requests in the name of the application (ladder/stash tabs)
DISCORD_CLIENT_ID=dummy                                 # discord oauth
DISCORD_CLIENT_SECRET=dummy                             # discord oauth
DISCORD_GUILD_ID=dummy                                  # id of the discord server
JWT_SECRET=dummy                                        # signing jwt tokens
PUBLIC_URL=http://localhost                             # used for oauth redirect urls
DISCORD_BOT_URL=http://localhost:9876/discord           # used for making http requests to the discord bot (internally over docker network)
KAFKA_BROKER=localhost:9092                             # kafka connection

# frontend
VITE_BACKEND_URL=http://localhost/api                   # used for making requests to the backend

# watchtower
WATCHTOWER_NOTIFICATION_URL=dummy                       # webhook url for watchtower notifications
" > local/.env

```

this will give you a rundown on the used variables, which applications need them and what they are used for.
All sensitive values are ommited.

## How to set this up locally

```
cd local
docker compose up -d
```
## Local development

to set up the infrastructure for local development, move to /local, create the .env file and then run

```
docker compose up -d
```

## Deployment

Once a change is pushed to the main branches of the backend/frontend/discord-bot repos, they trigger a github action to push newly build docker images to dockerhub and send an update request to watchtower.
The dockerhub repos are

- https://hub.docker.com/repository/docker/liberatorist/bpl2-frontend
- https://hub.docker.com/repository/docker/liberatorist/bpl2-backend
- https://hub.docker.com/repository/docker/liberatorist/bpl2-discord-bot

## Timescale DB Migration

We decided to install the timescaledb docker extension for character timeseries data.
If you're still running the old postgres database in docker compose, change the image and run

```
docker compose up -d
docker exec -it db bash
echo "shared_preload_libraries = 'timescaledb'" >> /var/lib/postgresql/data/postgresql.conf
docker restart db-local
```

connect to the database with psql and run

```
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

to add the extension.
