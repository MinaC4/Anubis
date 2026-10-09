import pytest

from anubis.utils.urls import is_safe_http_url


@pytest.mark.parametrize("url", [
    "http://example.org",
    "https://example.org/course?id=1",
    "http://192.168.1.8:30000/",
])
def test_safe_http_urls(url):
    assert is_safe_http_url(url)


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "https://user:password@example.org",
    "https://example.org/a b",
    "https://example.org\\@evil.test",
    "http://[::1",
    "http://example.org:99999",
    "https://example.org/path\nnext",
])
def test_reject_unsafe_http_urls(url):
    assert not is_safe_http_url(url)
