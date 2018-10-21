import pytest
import ouroboros.defaults as defaults

@pytest.mark.parametrize('default, result', [
    (defaults.INTERVAL, 300),
    (defaults.LOCAL_UNIX_SOCKET, 'unix://var/run/docker.sock'),
    (defaults.MONITOR, []),
    (defaults.LOGLEVEL, 'info'),
    (defaults.RUNONCE, False),
    (defaults.CLEANUP, False)
])

def test_defaults(default, result):
    assert default == result
