import pytest

import onvif
import onvif.client


def test_client_handle_errors():
    @onvif.client.handle_errors
    def maybe_raise(r=False):
        if r:
            raise Exception('oops')

        return 'ok'

    assert maybe_raise() == 'ok'

    with pytest.raises(
        onvif.ONVIFError,
        match='oops',
    ):
        maybe_raise(True)
