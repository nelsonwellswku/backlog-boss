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
npm run genclient
npm run dev
```

### And then...

Once both the backend and frontend are running, you can access the application and its OpenAPI documentation at the following URLs:

* [Frontend Website](http://localhost:5173)
* [API Docs](http://localhost:5173/api/docs)

## Docker

### Building the Docker Image

From the root directory, build the Docker image:

```bash
docker build -t backlog-boss .
```

This multi-stage build will:
1. Generate the OpenAPI schema from the backend
2. Generate the TypeScript client for the frontend
3. Build the frontend static files
4. Create a production image with both backend and frontend

### Running the Docker Container

Run the container with environment variables from your `.env` file:

```bash
docker run -p 9000:9000 \
  --add-host=host.docker.internal:host-gateway \
  -e DB_HOST="host.docker.internal" \
  -e DB_USER="$(grep DB_USER backend/.env | cut -d '=' -f2)" \
  -e DB_PASSWORD="$(grep DB_PASSWORD backend/.env | cut -d '=' -f2)" \
  -e TWITCH_CLIENT_ID="$(grep TWITCH_CLIENT_ID backend/.env | cut -d '=' -f2)" \
  -e TWITCH_CLIENT_SECRET="$(grep TWITCH_CLIENT_SECRET backend/.env | cut -d '=' -f2)" \
  -e STEAM_API_KEY="$(grep STEAM_API_KEY backend/.env | cut -d '=' -f2)" \
  backlog-boss
```

**Note:** The `--add-host` flag is required on Linux to allow the container to connect to the local database. On Mac/Windows, you can omit this flag.

Once running, access the application at:

* [Application](http://localhost:9000)
* [API Docs](http://localhost:9000/api/docs)
