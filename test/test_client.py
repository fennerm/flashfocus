"""Test suite for flashfocus.client."""
from __future__ import unicode_literals

from threading import Thread
from time import sleep

from pytest import raises

from flashfocus.client import client_request_flash


def test_client_request_flash(stub_server):
    p = Thread(target=stub_server.await_data)
    p.start()
    client_request_flash()
    sleep(0.05)
    p.join()
    assert stub_server.data == [b'1']

def test_client_request_flash_without_server():
    with raises(SystemExit) as error:
        client_request_flash()
        assert error.type == SystemExit
        import pytest
        pytest.set_trace()
