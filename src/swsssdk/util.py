"""
Syslog and daemon script utility library.
"""

from __future__ import print_function
import json
import logging
import logging.config
import sys
from getopt import getopt


# TODO: move to dbsync project.
def usage(script_name):
    print('Usage: python ', script_name,
          '-t [host] -p [port] -s [unix_socket_path] -d [logging_level] -f [update_frequency] -h [help]')


# TODO: move to dbsync project.
def process_options(script_name):
    """
    Process command line options
    """
    options, remainders = getopt(sys.argv[1:], "t:p:s:d:f:h", ["host=", "port=", "unix_socket_path=", "debug=", "frequency=", "help"])

    args = {}
    for (opt, arg) in options:
        try:
            if opt in ('-d', '--debug'):
                args['log_level'] = int(arg)
            elif opt in ('-t', '--host'):
                args['host'] = arg
            elif opt in ('-p', '--port'):
                args['port'] = int(arg)
            elif opt in ('-s', 'unix_socket_path'):
                args['unix_socket_path'] = arg
            elif opt in ('-f', '--frequency'):
                args['update_frequency'] = int(arg)
            elif opt in ('-h', '--help'):
                usage(script_name)
        except ValueError as e:
            print('Invalid option for {}: {}'.format(opt, e))
            sys.exit(1)

    return args


# TODO: move
def setup_logging(config_file_path, log_level=logging.INFO):
    """
    Logging configuration helper.

    :param config_file_path: file path to logging configuration file.
    https://docs.python.org/3/library/logging.config.html#object-connections
    :param log_level: defaults to logging.INFO
    :return: None - access the logger by name as described in the config--or the "root" logger as a backup.
    """
    try:
        with open(config_file_path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    except (ValueError, IOError, OSError):
        # json.JSONDecodeError is throwable in Python3.5+ -- subclass of ValueError
        logging.basicConfig(log_level=log_level)
        logging.root.exception(
            "Could not load specified logging configuration '{}'. Verify the filepath exists and is compliant with: "
            "[https://docs.python.org/3/library/logging.config.html#object-connections]".format(config_file_path))


def read_from_file(file_path, target_type=str):
    """
    Read content from file and convert to target type
    :param file_path: File path
    :param target_type: target type
    :return: content of the file according the target type.
    """
    value = None
    try:
        with open(file_path, 'r') as f:
            value = f.read()
            if value is None:
                # None return value is not allowed in any case, so we log error here for further debug.
                logging.error('Failed to read from {}, value is None, errno is {}'.format(file_path, ctypes.get_errno()))
                # Raise ValueError for the except statement to handle this as a normal exception
                raise ValueError('File content of {} is None'.format(file_path))
            else:
                value = target_type(value.strip())
    except (ValueError, IOError) as e:
        logging.error('Failed to read from {}, errno is {}'.format(file_path, str(e)))

    return value
