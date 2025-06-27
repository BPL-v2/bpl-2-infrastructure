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
- anything elese -> frontend

### Watchtower

Looks for new docker images for frontend/backend/discord-bot every 30 seconds and deploys them.

### Backend

https://github.com/BPL-v2/bpl-2-backend

### Discord Bot

https://github.com/BPL-v2/bpl-2-discord-bot

### Frontend

https://github.com/BPL-v2/bpl-2-fronend

## How to set this up locally

```
cd local
docker compose up -d
```

## Environment variables

We use a .env file for out environment variables.

/local/.env gives a rundown on the used variables, which applications need them and what they are used for.

All sensitive values are ommited.

## Deployment

Once a change is pushed to the main branches of the backend/frontend/discord-bot repos, they trigger a github action to push newly build docker images to dockerhub.
Watchtower queries dockerhub every 30 seconds and deploys any new versions automatically
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
