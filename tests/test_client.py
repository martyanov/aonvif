import pytest

import onvif
import onvif.client


def test_safe_func():
    @onvif.client.safe_func
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
