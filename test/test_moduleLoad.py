import os
import sys

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

from unittest import TestCase


class Test_load_connector_map(TestCase):
    def test__load_connector_map(self):
        # noinspection PyUnresolvedReferences
        import swsssdk

    def test__db_map_attributes(self):
        import swsssdk
        db2 = swsssdk.SonicV2Connector()
        self.assertTrue(all(hasattr(db2, db_name) for db_name in db2.db_map))
        pass
