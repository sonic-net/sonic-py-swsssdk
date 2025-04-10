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

    counters_db = 'COUNTERS_DB'
    host_ip = '127.0.0.1'

    def mocked_connect(db_id, db_name, retry_on):
        assert db_id == 2
        assert db_name == counters_db

    db.dbintf.connect = mocked_connect
    db.connect_host(counters_db, host_ip)

    assert db.dbintf.redis_kwargs["host"] == host_ip
    assert db.dbintf.redis_kwargs["port"] == 6379
