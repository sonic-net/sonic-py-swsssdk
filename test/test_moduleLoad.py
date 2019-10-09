import os
import sys

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

from unittest import TestCase


class Test_load_sonic_db_config(TestCase):
    def test__db_map_attributes(self):
        import swsssdk
        db = swsssdk.SonicV2Connector()
        self.assertTrue(all(hasattr(db, db_name) for db_name in db.get_db_list()))
        pass
