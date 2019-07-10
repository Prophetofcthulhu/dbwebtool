import aiopg
import logging
import async_timeout

from webdb.data_adapter.base_abstract_adaptor.base_adaptor import DatabaseAbstractSQLAdaptor

_logger = logging.getLogger(__name__)


def flatten_list(high_list):
    return [item for sublist in high_list for item in sublist]


class PostgreSQLAdaptorBased(DatabaseAbstractSQLAdaptor):
    DEFAULT_HOST = '193.24.30.63'
    DEFAULT_PORT = 53942
    DEFAULT_USER = 'admin'
    DEFAULT_PASSWORD = 'admin'

    CHECK_CONNECTION_TIMEOUT = 4
    DEFAULT_SELECT_LIMIT = 10000

    def __init__(self, loop, connection_string=None, **kwargs):
        if not connection_string:
            dbname = kwargs.pop("dbname", None)
            host = kwargs.pop("host", None) or self.DEFAULT_HOST
            port = kwargs.pop("port", None) or self.DEFAULT_PORT
            user = kwargs.pop("user", None) or self.DEFAULT_USER
            password = kwargs.pop("password", None) or self.DEFAULT_PASSWORD

            connection_string = f"dbname={dbname} user={user} password={password} host={host} port={port}"
        super().__init__(loop=loop, connection_string=connection_string, **kwargs)

    async def get_pool(self):
        if not self._pool:
            self._pool = await self.create_pool()
        return self._pool

    @staticmethod
    def compile_connection_string(dbname, user, password, host, port):
        return f"dbname={dbname} user={user} password={password} host={host} port={port}"

    @property
    def status_last_transaction(self):
        return self._cursor.statusmessage

    async def get_cursor(self, *args, **kwargs):
        if not self._cursor:
            self._cursor = await self.create_cursor()
        return self._cursor

    async def create_pool(self):
        try:
            with async_timeout.timeout(self.CHECK_CONNECTION_TIMEOUT):
                _logger.info("CREATING pool... Connection_string: '{}'".format(self.connection_string))
                self._pool = await aiopg.create_pool(self.connection_string)
                _logger.info("Pool CREATED")
            return self._pool
        except Exception as ex:
            _logger.warning("ERROR. Can not create pool. Exception: {}".format(ex))
            raise

    async def create_conn(self):
        try:
            with async_timeout.timeout(self.CHECK_CONNECTION_TIMEOUT):
                _logger.info("CREATING connection ...")
                pool = await self.get_pool()
                self._conn = await pool.acquire()
                _logger.info("Connection CREATED")
                return self._conn
        except Exception as ex:
            _logger.warning("ERROR. Cannot create Connection. Exception: {}".format(ex))
            raise

    async def create_cursor(self, *args, **kwargs):
        try:
            _logger.info("CREATING cursor ...")
            conn = await self.get_conn()
            self._cursor = await conn.cursor()
            _logger.info("Cursor CREATED")
            return self._cursor
        except Exception as ex:
            _logger.warning("ERROR. Cannot create Cursor. Exception: {}".format(ex))
            raise


class PostgreSQLAdaptor(PostgreSQLAdaptorBased):
    DEFAULT_SCHEMA_NAME = "test_db"
    SQL_TEMPLATES = {
        "SELECT": "SELECT {} from {} limit {} offset {}",
        "COUNT_ITEMS": "SELECT count(*) from {}",

        # "GET_SYSTEM_COLUMN_INFO": "SELECT {} FROM INFORMATION_SCHEMA.{}",
        "GET_COLUMN_INFO":     "SELECT column_name, udt_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}'",
        "GET_ALL_TABLE_NAMES": "SELECT table_name, table_catalog FROM INFORMATION_SCHEMA.tables WHERE table_type='BASE TABLE' AND table_schema='public'",
        "GET_ALL_VIEWS_NAMES": "select table_name, table_catalog from INFORMATION_SCHEMA.views WHERE table_schema = ANY (current_schemas(false))",
        "GET_SYSTEM_ALL_COLUMN_INFO":
            """SELECT c.table_name,
       c.column_name,
       c.udt_name,
       c.table_catalog,
       c.character_maximum_length,
       tc.constraint_type
FROM information_schema.COLUMNS c
left join information_schema.key_column_usage ksu
    on c.table_name = ksu.table_name
    and c.column_name = ksu.column_name
left join information_schema.table_constraints tc  on
    ksu.constraint_name = tc.constraint_name""",
        "WHERE_TABLE_NAME": """ WHERE c.table_name = '{}' and c.table_catalog='{}'"""
    }

    def __init__(self, loop, connection_string=None, **kwargs):
        super().__init__(loop, connection_string=connection_string, **kwargs)
        self.system_fields = {
            'COLUMNS': ["table_name",
                        "name",
                        "type",
                        "schema_name",
                        "character_maximum_length",
                        "constraint_type"],

        }
        self.tables = None
        self.views = None

    @staticmethod
    def prep_statement_insert_update(table_name, column_names, primary_key):
        columns_string = ", ".join(column_names)
        primary_key = ", ".join(primary_key) if isinstance(primary_key, list) else primary_key
        update_string = f"""ON CONFLICT ({primary_key}) 
        DO UPDATE """
        for column_name in column_names:
            update_string += f"""SET {column_name} = EXCLUDED.{column_name}
            """
        a = "{}"
        prepared_statement = f"""INSERT INTO {table_name} ({columns_string})
        VALUES ({a}) """+update_string
        return prepared_statement

    # TODO do it after schema
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
            return None

    async def create_field_list(self,
                                fields: list = None,
                                schema='public',
                                table_name="",
                                **kwargs):
        fields_info = kwargs.get("fields_info") or await self.get_column_info(schema=schema, table_name=table_name)
        model = []
        field_names = []
        for each in fields_info:
            if each["constraint_type"] == 'PRIMARY KEY':
                key = "PK"
            elif each["constraint_type"] == "FOREIGN KEY":
                key = "FK"
            else:
                key = ""
            model.append({
                "name": each["name"],
                "type": each["type"],
                "key": key
            })
            field_names.append(each["name"])
        return model, field_names

    async def _get_column_info(self, schema="test_db", table_name=""):
        schema_table_name = schema+"."+table_name
        if not self._columns_info.get(schema_table_name):
            sql = self.sql_template("GET_SYSTEM_ALL_COLUMN_INFO")+self.sql_template("WHERE_TABLE_NAME").format(table_name, schema)

            result = await self.execute_sql(sql)
            result_list = self.repack_as_dict(result, self.system_fields["COLUMNS"])
            _logger.debug("COLUMN INFO fot Table: '{}' {}".format(table_name, result_list))
            self._columns_info[schema_table_name] = result_list
        return self._columns_info[schema_table_name]

    async def get_column_info(self, table_name, schema=None):
        return await self._get_column_info(schema, table_name)

    # todo inject OTHER elements - likes 'functions', 'types' etc
    async def get_catalog(self, **kwargs):
        # schema = kwargs.get("schema") or self.DEFAULT_SCHEMA_NAME
        tables = [{"name": x[0], "type": "table", "schema": x[1]} for x in await self.get_all_table_names()]
        views  = [{"name": x[0], "type": "view", "schema": x[1]}  for x in await self.get_all_views_names()]
        return tables + views

    async def get_all_table_names(self):
        data = await self.execute_sql(self.sql_template("GET_ALL_TABLE_NAMES"))
        return data

    async def get_all_views_names(self):
        data = await self.execute_sql(self.sql_template("GET_ALL_VIEWS_NAMES"))
        return data

    async def select(self,
                     table_name: str,
                     fields: list = None,
                     limit: int = -1,
                     offset: int = 0,
                     **kwargs
                     ):
        fields_list = fields or []
        limit = self.DEFAULT_SELECT_LIMIT if limit == -1 else limit
        schema = kwargs.get("schema") or None

        if not fields_list:
            fields_info = kwargs.get("fields_info") or await self.get_column_info(schema, table_name)

            for each in fields_info:
                fields_list.append(each["name"])

        # todo - use PREPARE STATEMENT & BIND here
        fields_str = ", ".join(fields_list)
        sql = self.sql_template("SELECT").format(fields_str, table_name, limit, offset)

        return await self.execute_sql(sql)

