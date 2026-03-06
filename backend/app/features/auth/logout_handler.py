from fastapi import Request, Response
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import AppSession


class LogoutHandler:
    def __init__(self, db_session: DbSession, request: Request):
        self.db_session = db_session
        self.request = request

    def handle(self):
        session_key = self.request.cookies.get("session_key")
        if session_key:
            app_session = self.db_session.scalars(
                select(AppSession).where(AppSession.app_session_key == session_key)
            ).one_or_none()
            if app_session:
                self.db_session.delete(app_session)
                self.db_session.commit()

        response = Response()
        response.delete_cookie("session_key")

        return response
