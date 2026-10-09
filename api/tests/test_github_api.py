from unittest.mock import patch

import requests

from anubis.github.api import github_rest


def test_github_rest_rejects_http_errors(monkeypatch):
    response = requests.Response()
    response.status_code = 500
    response.url = "https://api.github.com/repos/example/course"
    response._content = b"server error"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    with patch("anubis.github.api.requests.delete", return_value=response):
        assert github_rest("/repos/example/course", method="delete") is None


def test_github_rest_accepts_empty_delete_success(monkeypatch):
    response = requests.Response()
    response.status_code = 204
    response.url = "https://api.github.com/repos/example/course"
    response.headers["Content-Type"] = "application/json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    with patch("anubis.github.api.requests.delete", return_value=response):
        assert github_rest("/repos/example/course", method="delete") == {}
