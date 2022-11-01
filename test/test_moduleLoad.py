import os
import sys

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

from unittest import TestCase
import subprocess

class Test_load_sonic_db_config(TestCase):
    def test__db_map_attributes(self):
        import swsssdk
        db = swsssdk.SonicV2Connector()
        self.assertTrue(all(hasattr(db, db_name) for db_name in db.get_db_list()))

    # This is the test to check if the global config file extraction of namespace is correct.
    def test__namespace_list(self):
        import swsssdk
        dbConfig = swsssdk.SonicDBConfig()
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), './config', 'database_global.json')
        dbConfig.load_sonic_global_db_config(global_db_file_path=filepath)
        ns_input = ['', 'asic0', 'asic1', 'asic2']
        ns_list = list(dbConfig.get_ns_list())
        ns_input.sort()
        ns_list.sort()
        self.assertEqual(ns_input, ns_list)

    # This is the test to check if the global config file and get the correct DB in a namespace
    def test__dbConfig(self):
        import swsssdk
        dbConfig = swsssdk.SonicDBConfig()
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), './config', 'database_global.json')
        dbConfig.load_sonic_global_db_config(global_db_file_path=filepath)
        for namespace in list(dbConfig.get_ns_list()):
            self.assertEqual(dbConfig.get_dbid('PFC_WD_DB', namespace), 5)
            self.assertEqual(dbConfig.get_dbid('APPL_DB', namespace), 0)

def test_BlockUseSwsssdk():
    # Import swsssdk will throw exception with deprecated message.
    swsssdk_path = os.path.join(modules_path, 'src')
    result = None
    python_command = "python"
    
    if sys.version_info.major == 3:
        python_command = "python3"

    try:
        subprocess.check_output([python_command, "-c", "import swsssdk;exit()"], stderr=subprocess.STDOUT, cwd=swsssdk_path)
    except subprocess.CalledProcessError as e:
        result = e.output.decode("utf-8")

    assert "deprecated" in result
