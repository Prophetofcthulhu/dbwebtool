import re
import time
import asyncio
import logging
import aiosqlite

from sysutils.utils.debug import nice_print

from data_adapter.base_abstract_adaptor.base_adaptor import DatabaseAbstractSQLAdaptor

_logger = logging.getLogger(__name__)


class SqliteBaseAdaptorBase(DatabaseAbstractSQLAdaptor):
    def __init__(self, loop, database_file_path, **kwargs):
        super().__init__(loop, database_file_path, **kwargs)

    @staticmethod
    def compile_connection_string(host, **kwargs):
        return host

    async def create_pool(self):
        return self

    async def get_pool(self):
        pass

    async def create_conn(self):
        self._conn = await aiosqlite.connect(self.db_path, loop=self.loop)
        return self._conn

    async def create_cursor(self, sql, **kwargs):
        conn = await self.get_conn()
        self._cursor = await conn.execute(sql)
        return self._cursor

    @property
    def db_path(self):
        return self.connection_string

    @classmethod
    def clear_connection_string(cls, connection_string):
        return connection_string


class SqliteBaseAdaptor(SqliteBaseAdaptorBase):
    MASTER_TABLE = "sqlite_master"
    SQL_TEMPLATES = {
        "COUNT_ITEMS": "SELECT count(*) from {}",
        "SELECT": "SELECT {} from {} limit {} offset {}",
        "GET_SYSTEM_COLUMN_INFO": "SELECT {} FROM {}",
        "PRAGMA": "PRAGMA table_info({})",
        "FOREIGN_KEY": "PRAGMA foreign_key_list({})",
        "WHERE": " where tbl_name='{}'"
    }

    def __init__(self, loop, database_file_path, **kwargs):
        super().__init__(loop, database_file_path, **kwargs)
        self.system_fields = {
            'sqlite_master': ['type', 'name'], #, 'sql'],
            'pragma': ['cid', 'name', 'type', 'not_null', 'dflt_value', 'primary'],
            'foreign_key': ["id", "seq", "table_name", "name", "ref_column", "on_update", "on_delete", "match"]
        }
        self._tables_info = []

    @staticmethod
    def prep_statement_insert_update(table_name, column_names, primary_key):
        columns_string = ", ".join(column_names)
        primary_key = ", ".join(primary_key) if isinstance(primary_key, list) else primary_key
        update_string = f"""ON CONFLICT ({primary_key}) 
        DO UPDATE """
        for column_name in column_names:
            update_string += f"""SET {column_name} = excluded.{column_name}
            """
        a = "{}"
        prepared_statement = f"""INSERT INTO {table_name} ({columns_string})
        VALUES ({a}) """+update_string
        return prepared_statement

    async def execute_insert_update(self,
                                    table_name,
                                    column_names,
                                    values,
                                    schema=None,
                                    primary_key=None,
                                    *args, **kwargs):
        if self.read_only:
            _logger.info("Read Only Connection. CAnnot insert or update")
            return None
        if schema:
            table_name = schema + "." + table_name
        values_string = ", ".join(values)
        sql = self.prep_statement_insert_update(table_name,
                                                column_names,
                                                primary_key
                                                ).format(values_string)
        try:
            return await self.execute_sql(sql)
        except Exception as error:
            _logger.warning("Cannot execute SQL '{}'; Exception: {}".format(sql, error))
            return error

    async def get_catalog(self, **kwargs):
        if not self._tables_info:

            fields = self.system_fields[self.MASTER_TABLE]
            fields_str = ",".join(fields)
                # if table_name:
            sql = self.sql_template("GET_SYSTEM_COLUMN_INFO").format(fields_str, self.MASTER_TABLE)
            result = await self.execute_sql(sql)

            self._tables_info = self.repack_as_dict(result, fields)

            _logger.debug("SYSTEM COLUMN INFO fot Table: '{}' {}".format(self.MASTER_TABLE, self._tables_info))
            for each in self._tables_info:
                await self.get_column_info(each['name'])
        return self._tables_info

    async def create_field_list(self,
                                fields: list = None,
                                schema='public',
                                table_name="",
                                **kwargs):
        return await self.get_column_info(schema=schema, table_name=table_name)

    async def get_foreign_keys(self, table_name) -> list:
        fields = self.system_fields['foreign_key']
        sql = self.sql_template("FOREIGN_KEY").format(table_name)
        result = await self.execute_sql(sql)
        return self.repack_as_dict(result, fields)

    async def get_column_info(self, table_name, *args, **kwargs):
        # if not self._columns_info.get(table_name):
        fields = self.system_fields['pragma']
        sql = self.sql_template("PRAGMA").format(table_name)
        result = await self.execute_sql(sql)
        result = self.repack_as_dict(result, fields)
        foreign_key = await self.get_foreign_keys(table_name)
        result1, field_names = [], []
        for each in result:
            if each["primary"] == 1:
                each["key"] = "PK"
            del each["primary"]
            if isinstance(foreign_key, list):
                for row in foreign_key:
                    if each["name"] == row["name"]:
                        each = {**each, **row}
                        each["key"] = "FK"
            elif isinstance(foreign_key, dict):
                if foreign_key["name"] == each["name"]:
                    each = {**each, **foreign_key}
                    each["key"] = "FK"
            result1.append(each)
            field_names.append(each["name"])

        self._columns_info[table_name] = result1
        return self._columns_info[table_name], field_names
