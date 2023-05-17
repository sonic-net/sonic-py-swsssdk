import os
import sys
import pytest
if sys.version_info.major == 3:
    from unittest import mock
else:
    import mock
from mock import patch, MagicMock

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))
import swsssdk

class TestSonicDbDumpLoad(object):
    def setup(self):
        print("SETUP")

    @patch('optparse.OptionParser.print_help')
    @patch('optparse.OptionParser.parse_args', MagicMock(return_value=('options', ['-p'])))
    @patch('sys.argv', ['dump'])
    def test_sonic_db_dump_exit(self, mock_print_help):
        with pytest.raises(SystemExit) as e:
            swsssdk.sonic_db_dump_load()
        mock_print_help.assert_called_once()
        assert e.value.code == 4

    @patch('optparse.OptionParser.print_help')
    @patch('optparse.OptionParser.parse_args', MagicMock(return_value=('options', ['-p', '-o'])))
    @patch('sys.argv', ['load'])
    def test_sonic_db_load_exit(self, mock_print_help):
        with pytest.raises(SystemExit) as e:
            swsssdk.sonic_db_dump_load()
        mock_print_help.assert_called_once()
        assert e.value.code == 4

    def teardown(self):
        print("TEARDOWN")

