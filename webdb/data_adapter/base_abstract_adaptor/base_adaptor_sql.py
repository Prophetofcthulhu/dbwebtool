from abc import ABCMeta, abstractmethod
import async_timeout
import re
from sysutils.utils.timer import Timer

from logging import getLogger
_logger = getLogger(__name__)

from .base_adaptor import DatabaseAbstractAdaptor


class DatabaseAbstractSQLAdaptor(DatabaseAbstractAdaptor):
    SQL_TEMPLATES = {}
    DEFAULT_SELECT_LIMIT = 10000
    CHECK_CONNECTION_TIMEOUT = 5
    COUNT_ITEM_TIMEOUT = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._pool = None
        self._conn = None
        self._cursor = None

        self._columns_info = {}  # caching for system table
        self.system_fields = {
            # 'TABLE_NAME': ['column_name', 'udt_name'],
        }

    @classmethod
    def sql_template(cls, request_selector):
        return cls.SQL_TEMPLATES[request_selector]

    @abstractmethod
    async def create_pool(self):
        """Create pool should be implemented"""

    @abstractmethod
    async def create_conn(self):
        """Create conn should be implemented"""

    @abstractmethod
    async def create_cursor(self, *args, **kwargs):
        """Create cursor should be implemented"""

    async def close_pool(self):
        if self._pool and self._pool is not self:
            self._pool.closeall()
            self._pool = None

    @abstractmethod
    async def get_pool(self):
        """ Close pool """

    async def get_conn(self):
        if not self._conn:
            self._conn = await self.create_conn()
        return self._conn

    async def get_cursor(self, *args, **kwargs):
        if not self._cursor:
            self._cursor = await self.create_cursor(*args, **kwargs)
        return self._cursor

    async def ping(self) -> int:
        """ Check if database online & available for connection """
        try:
            with Timer() as timer:
                with async_timeout.timeout(self.CHECK_CONNECTION_TIMEOUT):
                    await self.create_pool()
                    # await self.close_pool()
            self._ping_time = timer.elapsed()
            return self._ping_time

        except Exception as ex:
            _logger.info("Ping failure in timeout {} sec.".format(self.CHECK_CONNECTION_TIMEOUT))
            return -1

    async def count_items(self, table_name, schema=""):
        try:
            with async_timeout.timeout(self.COUNT_ITEM_TIMEOUT):
                sql = self.sql_template("COUNT_ITEMS").format(table_name)
                row = await self.execute_select(sql)
                count = row[0][0]
                return count

        except Exception as ex:
            _logger.info("Ping failure in timeout {} sec.".format(self.CHECK_CONNECTION_TIMEOUT))
            return -1

    @abstractmethod
    async def get_column_info(self, table_name, schema=None):
        # # TODO schema(keyspace)
        if schema:
            table_name = schema+'.'+table_name
        if not self._columns_info.get(table_name):
            fields = self.system_fields[table_name]
            fields_str = ",".join(fields)
            sql = self.sql_template("GET_SYSTEM_COLUMN_INFO").format(fields_str, table_name)
            result = await self.execute_sql(sql)

            result_list = self.repack_as_dict(result, fields)

            _logger.debug("SYSTEM COLUMN INFO fot Table: '{}' {}".format(table_name, result_list))

            self._columns_info[table_name] = result_list
        return self._columns_info[table_name]
        # raise Exception("Not Implemented")

    async def create_field_list(self,
                                fields: list = None,
                                schema='public',
                                table_name="",
                                **kwargs):
        fields_info = kwargs.get("fields_info") or await self.get_column_info(schema=schema, table_name=table_name)
        field_names = [each["name"] for each in fields_info]
        return fields_info, field_names

    async def execute_sql(self, sql):
        try:
            if self.read_only and not self.is_read_only_request(sql):
                _logger.info("Read Only Connection. SQL \n '{}'\n SKIPPED".format(sql))
                return None

            _logger.debug(f"EXECUTING SQL '{sql}' ...")

            cursor = await self.get_cursor(sql)
            await cursor.execute(sql)
            result = await cursor.fetchall()
            _logger.debug("COMPLETED. Number of records: [{}]".format(len(result)))
            return result

        except Exception as error:
            _logger.warning("Cannot execute SQL '{}'; Exception: {}".format(sql, error))
            return None

    # todo remove / rewrite  this method ???
    async def execute_select(self, sql, **kwargs):
        try:
            _logger.debug(f"EXECUTING '{sql}' ...")
            cursor  = await self.get_cursor(sql)
            await cursor.execute(sql)
            rows    = await cursor.fetchall()
            _logger.debug("COMPLETED. Number of records: [{}]".format(len(rows)))
            return rows
        except Exception as ex:
            _logger.warning("Cannot Select data from Table; Exception: {}".format(ex))
            return None

    async def fetch(self,
                     table_name: str,
                     schema: (str, None) = None,
                     fields: list = None,
                     limit: int = -1,
                     offset: int = 0,
                     condition: str = None,
                     **kwargs
                     ) -> (dict, dict):
        limit = self.DEFAULT_SELECT_LIMIT if limit == -1 else limit

        # todo Implement condition
        # todo - use PREPARE STATEMENT & BIND here
        """
        http://initd.org/psycopg/docs/cursor.html
        "select * from TABLE where name = ?"

        """
        with Timer() as timer:
            models, field_names = await self.create_field_list(fields, schema=schema, table_name=table_name, **kwargs)
            fields_str = ", ".join(field_names)
            sql = self.sql_template("SELECT").format(fields_str, table_name, limit, offset)
            data = await self.execute_sql(sql)
        meta = {
            "time": timer.elapsed,
            "sql": sql,
            "model": models,
        }
        return data, meta

    @classmethod
    def clear_connection_string(cls, connection_string):
        temp = []
        for param in connection_string.split(" "):
            if param.startswith("password"):
                param = "password=***"
            temp.append(param)

    @staticmethod
    def is_read_only_request(sql) -> bool:
        regex = '^(select|pragma).*'
        result = re.search(regex, sql.lower())
        _logger.info(f"is_read_only_request    '{type(result)}'")
        return bool(result)

    @staticmethod
    def sql_for_create_table(table_name, table_params_fields: list) -> str:
        sql_base = "CREATE TABLE {} ".format(table_name)
        sql_list = []

        for item in table_params_fields:
            sql_piece = "{} {} ".format(item["name"], item["type"])
            if item.get("PK"):
                sql_piece += " PRIMARY KEY "
            sql_list.append(sql_piece)
        sql_pieces = ", ".join(sql_list)
        sql = sql_base + '( ' + sql_pieces + ')'
        return sql

    async def create_table_model(self, table_name, model):
        try:
            if not self.read_only:
                sql = self.sql_for_create_table(table_name, model)
                cursor = await self.get_cursor()
                await cursor.execute(sql)
            else:
                _logger.info("Read only connection. Create table '{}'  SKIPPED".format(table_name))
        except Exception as error:
            _logger.warning("Cannot create Table '{}'. Exception: {}".format(table_name, error))

    @staticmethod
    def compose_empty_row(tab_fields):
        return {x: "" for x in tab_fields}
