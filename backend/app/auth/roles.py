from app.auth.permissions import Permission, Resource

ROLES: dict[str, dict[str, list[str]]] = {
    "admin": {
        Resource.IGDB_GAMES: [Permission.READ, Permission.WRITE],
    },
    "user": {},
}
