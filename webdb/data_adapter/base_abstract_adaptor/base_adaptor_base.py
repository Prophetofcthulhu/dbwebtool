from abc import ABCMeta, abstractmethod
import asyncio
import re
from core.utils import repack_as_dict

from logging import getLogger
_logger = getLogger(__name__)


class DatabaseAbstractAdaptor(metaclass=ABCMeta):
    def __init__(self, loop, connection_string, **kwargs):
        self._loop = loop
        self._connection_string = connection_string
        self._queue = asyncio.queues.Queue(loop=self._loop)
        self.read_only = kwargs.get("read_only") or True
        self._ping_time = 1

    @classmethod
    def clear_connection_string(cls, connection_string):
        raise NotImplemented("clear_connection_string")

    @property
    def connection_string(self):
        return self._connection_string

    @property
    def safe_connection_string(self):
        return self.clear_connection_string(self.connection_string)

    @property
    def loop(self):
        return self._loop

    @property
    def ping_time(self):
        return self._ping_time

    @abstractmethod
    async def ping(self) -> int:
        """ Check if database online & available for connection
            returns number of tick -> the less value for faster connection
        """

    @abstractmethod
    async def create_table_model(self, table_name, model):
        raise NotImplementedError()

    @abstractmethod
    async def execute_select(self, sql: str, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    async def execute_insert_update(self,
                                    table_name,
                                    column_names,
                                    values,
                                    schema=None,
                                    primary_key=None,
                                    *args, **kwargs):
        raise NotImplementedError()


    @abstractmethod
    async def get_catalog(self, **kwargs) -> list:
        raise NotImplementedError()

    @abstractmethod
    async def fetch(self,
                    table_name: str,
                    schema: (str, None) = None,
                    fields: list = None,
                    limit: int = -1,
                    offset: int = 0,
                    condition: str = None,
                    **kwargs) -> (dict, dict):
        """ Fetch DATA from a Table"""

    async def count_items(self, table_name, schema=""):
        return 0

    @staticmethod
    def compile_connection_string(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def repack_as_dict(rows, fields):
        return repack_as_dict(rows, fields)
