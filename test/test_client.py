"""Test suite for flashfocus.client."""
import sys
from threading import Thread

from flashfocus.client import client_request_flash


def test_client_request_flash(stub_server):
    p = Thread(target=stub_server.await_data)
    p.start()
    client_request_flash()
    p.join()
    if sys.version_info[0] > 2:
        assert stub_server.data == [b'1']
    else:
        assert stub_server.data == ['1']
