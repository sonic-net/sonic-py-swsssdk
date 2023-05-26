import os
import sys

from unittest import mock

from unittest import TestCase

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

import swsssdk
import fakeredis


class TestConfigDB(TestCase):
    def test__configdb_pipe(self):

        s_db = swsssdk.ConfigDBPipeConnector()
        #Use fakeredis to mock redis db
        r_db = fakeredis.FakeStrictRedis(version=5)
        s_db.get_redis_client = lambda db_name: r_db
        s_db.db_name = "CONFIG_DB"

        s_db.mod_config({'TABLE_NAME': { 'row_key': {'column_key1': 'valueA1', 'column_key2': 'valueB1'}}})
        self.assertEqual(r_db.hget('TABLE_NAME|row_key', 'column_key1'), b'valueA1')
        self.assertEqual(r_db.hget('TABLE_NAME|row_key', 'column_key2'), b'valueB1')
        s_db.mod_config({'TABLE_NAME': { 'row_key': {'column_key1': 'valueA2'}}}, table_delete='TABLE_NAME')
        self.assertEqual(r_db.hget('TABLE_NAME|row_key', 'column_key1'), b'valueA2')
        self.assertEqual(r_db.hget('TABLE_NAME|row_key', 'column_key2'), None)
        
        
