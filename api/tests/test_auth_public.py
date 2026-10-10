from types import SimpleNamespace

from flask import Flask
import pytest
from werkzeug.security import generate_password_hash

from anubis.env import env
from anubis.utils.exceptions import AuthenticationError
from anubis.views.public import auth


def test_personal_github_link_requires_an_anubis_user(monkeypatch):
    monkeypatch.setattr(env, "LOCAL_AUTH_USERNAME", "mina")
    app = Flask(__name__)

    with app.test_request_context("/api/public/github/login"):
        with pytest.raises(AuthenticationError):
            auth.public_github_link()


def test_local_student_can_sign_in_with_its_password(monkeypatch):
    student = SimpleNamespace(netid="student1", disabled=False, local_password_hash=generate_password_hash("student-password-123"))

    class UserQuery:
        def filter_by(self, **kwargs):
            assert kwargs == {"netid": "student1"}
            return self

        def first(self):
            return student

    monkeypatch.setattr(env, "LOCAL_AUTH_USERNAME", "mina")
    monkeypatch.setattr(env, "LOCAL_AUTH_PASSWORD", "admin-password")
    monkeypatch.setattr(auth.User, "query", UserQuery())
    monkeypatch.setattr(auth, "create_token", lambda netid: f"token-for-{netid}")
    app = Flask(__name__)
    app.add_url_rule("/login", view_func=auth.public_login, methods=["GET", "POST"])

    response = app.test_client().post("/login", data={"username": "student1", "password": "student-password-123"})

    assert response.status_code == 302
    assert response.location == "/"
    assert response.headers["Set-Cookie"].startswith("token=token-for-student1;")


def test_github_oauth_requires_study_access_code_for_anonymous_user(monkeypatch):
    monkeypatch.setattr(env, "LOCAL_AUTH_USERNAME", None)
    monkeypatch.setattr(auth, "get_config_str", lambda *_args: None)
    app = Flask(__name__)

    with app.test_request_context("/api/public/github/login"):
        with pytest.raises(AuthenticationError):
            auth.public_github_link()


def test_github_oauth_callback_creates_anonymous_user(monkeypatch):
    class UserQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return None

    class GithubResponse:
        def json(self):
            return {"id": 123, "login": "mina", "name": "Mina"}

    added = []
    monkeypatch.setattr(auth, "get_current_user", lambda: None)
    monkeypatch.setattr(auth.github_provider, "authorized_response", lambda: {"access_token": "token"})
    monkeypatch.setattr(auth.requests, "get", lambda *_args, **_kwargs: GithubResponse())
    monkeypatch.setattr(auth.User, "query", UserQuery())
    monkeypatch.setattr(auth.db, "session", SimpleNamespace(add=added.append, commit=lambda: None))
    monkeypatch.setattr(auth, "create_token", lambda netid: f"token-for-{netid}")
    app = Flask(__name__)

    with app.test_request_context("/api/public/github/oauth"):
        response = auth.public_github_oauth()

    assert response.location == "/profile"
    assert response.headers["Set-Cookie"].startswith("token=token-for-github123;")
    assert added[0].netid == "github123"
    assert added[0].github_username == "mina"
