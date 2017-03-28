class SwSSQueryError(Exception):
    """ Base exception class """


class UnavailableDataError(SwSSQueryError):
    def __init__(self, message, data, *args, **kwargs):
        super(UnavailableDataError, self).__init__(message, *args, **kwargs)
        """
        In Python2:
        # default strings are ascii (or byte [b'']) strings
        >>> type(b'port_name_map')
        <type 'str'>
        >>> type('port_name_map')
        <type 'str'>
        >>> 'port_name_map'.encode('ascii')
        'port_name_map'
        >>> type('test') is bytes
        True

        In Python3:
        # default strings are unicode
        >>> type('port_name_map')
        <class 'str'>
        >>> type(b'port_name_map')
        <class 'bytes'>
        >>> 'port_name_map'.encode('ascii')
        b'port_name_map'
        >>> type(b'test') is bytes
        True


        Redis /always/ utilizes byte-strings regardless of Python version.
        This cast ensures consistency across all platforms when waiting for available data.

        {
           'data': b'hset',
           'channel': b'__keyspace@0__:0000000100000020',
           'pattern': b'__key*__:*',
           'type': 'pmessage'
        }
        """
        self.data = data if type(data) is bytes else data.encode('ascii')


class MissingClientError(SwSSQueryError):
    """ Raised when a queried client wasn't found. """
