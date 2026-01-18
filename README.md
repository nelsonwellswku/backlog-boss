# Backlog Boss
Video game backlog prioritizer

## Development

### Prerequisites
* [uv](https://docs.astral.sh/uv/)
* [node](https://nodejs.org)
* [docker](https://docker.com)

### Database

The database is SQL Server. [grate](https://github.com/grate-devs/grate) creates the local database and runs the database migrations.

From the root directory, run:

```
docker compose up
```

### Backend

Navigate to `/backend` and then run:

```
uv sync
fastapi dev main.py
```

For additional information, see the [backend readme](./backend/README.md).

### Frontend

Navigate to `/backend` and then run:

```
python export_openapi.py
```

This will generate an appropriate OpenAPI specification from which to generate the Typescript client.

Next, Navigate to `/frontend` and then run:

```
npm install
px @hey-api/openapi-ts -i ../backend/openapi.json -o src/client
npm run dev
```

### And then...

Once the backend and frontend are running, the application, including OpenAPI docs can be accessed.

* [Frontend Website](http://localhost:5173)
* [API Docs](http://localhost:5713/api/docs)
