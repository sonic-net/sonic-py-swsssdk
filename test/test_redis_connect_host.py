import os
import sys

if sys.version_info.major == 3:
    from unittest import mock
else:
    import mock

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

from swsssdk import SonicV2Connector

def test_redis_connect_host():
    mock_dbintf = mock.MagicMock()
    db = SonicV2Connector()
    db.dbintf = mock_dbintf
    db.dbintf.redis_kwargs = {}

    db_name = 'COUNTERS_DB'
    host = '127.0.0.1'

    db.connect_host(db_name, host)
    mock_dbintf.connect.assert_called_once_with(2, db_name, True)

    assert db.dbintf.redis_kwargs["host"] == host
    assert db.dbintf.redis_kwargs["port"] == 6379
