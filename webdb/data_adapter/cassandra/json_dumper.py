import json
import datetime
import decimal
import uuid
import six
import collections
import logging

from cassandra.util import OrderedMapSerializedKey, SortedSet

# from sysutils.json_tools import json_dumps
from sysutils.utils.json_tools import json_dumps as _json_dumps
from sysutils.utils.json_tools import json_loads as _json_loads

_logger = logging.getLogger(__name__)

# JSONDecoder

class CassandraJsonEncoder(json.JSONEncoder):
    """
    Based on REST Framework JSONEncoder
    .venv/lib/python3.7/site-packages/rest_framework/utils/encoders.py
    """
    def default(self, obj):
        try:
            if isinstance(obj, datetime.datetime):
                representation = obj.isoformat()
                if representation.endswith('+00:00'):
                    representation = representation[:-6] + 'Z'
                return representation
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, datetime.time):
                return obj.isoformat()
            elif isinstance(obj, datetime.timedelta):
                return six.text_type(obj.total_seconds())
            elif isinstance(obj, decimal.Decimal):
                return float(obj)
            elif isinstance(obj, uuid.UUID):
                return six.text_type(obj)
            elif isinstance(obj, OrderedMapSerializedKey):
                return dict(obj)
            elif isinstance(obj, (collections.Set, SortedSet)):
                return tuple(obj)
            elif isinstance(obj, bytes):
                return obj.decode('utf-8')
            elif hasattr(obj, 'tolist'):
                return obj.tolist()     # Numpy arrays and array scalars.
            elif hasattr(obj, '__getitem__'):
                return dict(obj)
            elif hasattr(obj, '__iter__'):
                return tuple(item for item in obj)
            return super().default(obj)
        except Exception as ex:
            #print("EX: type: {} obj: {} Ex: {}".format(type(obj), obj, ex))
            return str(obj)


def json_dumps(data: [list, dict], **kwargs) -> str:
    return _json_dumps(data, cls=CassandraJsonEncoder, **kwargs)


def json_loads(data_as_string: str, **kwargs) -> [list, dict]:
    return _json_loads(data_as_string, cls=CassandraJsonEncoder, **kwargs)