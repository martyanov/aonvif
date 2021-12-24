import pytest

import aonvif
import aonvif.client


def test_client_handle_errors():
    @aonvif.client.handle_errors
    def maybe_raise(r=False):
        if r:
            raise Exception('oops')

        return 'ok'

    assert maybe_raise() == 'ok'

    with pytest.raises(
        aonvif.ONVIFError,
        match='oops',
    ):
        maybe_raise(True)
