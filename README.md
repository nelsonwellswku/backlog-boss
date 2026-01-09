# Backlog Boss
Video game backlog prioritizer

## Development

### Prerequisites
* [uv](https://docs.astral.sh/uv/)
* Node and NPM

### Backend

Navigate to `/backend` and then run:

```
uv sync
fastapi dev main.py
```

For additional information, see the [backend readme](./backend/README.md).

### Frontend

Ensure the backend is running. This is necessary to generate the Typescript client.

Navigate to `/frontend` and then run:

```
npm install
npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/client
npm run dev
```
