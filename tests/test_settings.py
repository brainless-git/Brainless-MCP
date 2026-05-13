"""Tests for the settings / configuration module."""

import pytest
from brainless_mcp.config.settings import Settings


def test_default_graphql_url():
    s = Settings(unraid_api_url="https://192.168.1.100")
    assert s.graphql_url == "https://192.168.1.100/graphql"


def test_trailing_slash_stripped():
    s = Settings(unraid_api_url="https://tower.local/")
    assert s.graphql_url == "https://tower.local/graphql"


def test_ws_url_https_to_wss():
    s = Settings(unraid_api_url="https://tower.local")
    assert s.ws_url == "wss://tower.local/graphql"


def test_ws_url_http_to_ws():
    s = Settings(unraid_api_url="http://tower.local")
    assert s.ws_url == "ws://tower.local/graphql"


def test_ssl_verify_false():
    s = Settings(unraid_verify_ssl="false")
    assert s.ssl_verify is False


def test_ssl_verify_true():
    s = Settings(unraid_verify_ssl="true")
    assert s.ssl_verify is True


def test_ssl_verify_ca_bundle():
    s = Settings(unraid_verify_ssl="/etc/ssl/ca.pem")
    assert s.ssl_verify == "/etc/ssl/ca.pem"
