import aiomysql
import logging
import async_timeout
import re

from webdb.data_adapter.base_abstract_adaptor.base_adaptor import DatabaseAbstractSQLAdaptor

_logger = logging.getLogger(__name__)


def flatten_list(high_list):
    return [item for sublist in high_list for item in sublist] if high_list else []


class MySQLAdaptorBased(DatabaseAbstractSQLAdaptor):
    DEFAULT_HOST = '193.24.30.63'
    DEFAULT_PORT = 6603
    DEFAULT_USER = 'root'
    DEFAULT_PASSWORD = '****'
    DEFAULT_DB_NAME = 'public'

    CHECK_CONNECTION_TIMEOUT = 4
    DEFAULT_SELECT_LIMIT = 500

    def __init__(self, loop, connection_string=None, **kwargs):
        if not connection_string:
            host = kwargs.pop("host", None) or self.DEFAULT_HOST
            port = kwargs.pop("port", None) or self.DEFAULT_PORT
            user = kwargs.pop("user", None) or self.DEFAULT_USER
            password = kwargs.pop("password", None) or self.DEFAULT_PASSWORD
            db = kwargs.pop("db", None) or self.DEFAULT_DB_NAME

            connection_string = f"db={db} user={user} password={password} host={host} port={port}"
        else:
            host_regex = r"(?<=host=)[a-zA-Z0-9.\[\],]*"
            port_regex = r"(?<=port=)[a-zA-Z0-9.]*"
            password_regex = r"(?<=password=)[a-zA-Z0-9.\[\],!@#$%^&*()_\-+=|\\]*"
            user_regex = r'(?<=user=)[a-zA-Z0-9.]*'
            db_regex = r'(?<=db=)[a-zA-Z0-9.]*'


            host =      re.search(host_regex,     connection_string)
            port =      re.search(port_regex,     connection_string)
            password =  re.search(password_regex,  connection_string)
            user =      re.search(user_regex,      connection_string)
            db =        re.search(db_regex,        connection_string)

            host =      host.group(0)
            port =      port.group(0)
            db =        db.group(0) if db else None
            user =      user.group(0) if user else None
            password =  password.group(0) if password else None
            if host[0] == "[":
                hosts = host[1:-1]
                host = hosts.split(",")

        self.host = host
        # self.host = 'localhost'
        self.port = int(port)
        self.user = user
        self.password = password
        self.db = db
        # self.db = None

        super().__init__(loop=loop, connection_string=connection_string, **kwargs)


    @staticmethod
    def compile_connection_string(dbname, user, password, host, port):
        return f"db={dbname} user={user} password={password} host={host} port={port}"

    async def get_pool(self):
        if not self._pool:
            self._pool = await self.create_pool()
        return self._pool

    @property
    def status_last_transaction(self):
        return self._cursor.statusmessage

    async def create_pool(self):
        try:
            with async_timeout.timeout(self.CHECK_CONNECTION_TIMEOUT):
                _logger.info("CREATING pool... Connection_string: '{}'".format(self.connection_string))
                self._pool = await aiomysql.create_pool(db=self.db,
                                                        user=self.user,
                                                        password=self.password,
                                                        host=self.host,
                                                        port=self.port,
                                                        loop=self.loop)
                _logger.info("Pool Created")
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


class MySQLAdaptor(MySQLAdaptorBased):
    DEFAULT_SCHEMA_NAME = "public"
    SQL_TEMPLATES = {
        "SELECT": "SELECT {} from {} limit {} offset {}",
        "COUNT_ITEMS": "SELECT count(*) from {}",
         "GET_SYSTEM_COLUMN_INFO": "SELECT {} FROM INFORMATION_SCHEMA.{}",
        "GET_COLUMN_INFO":
        # "SELECT COLUMN_NAME, DATA_TYPE, table_schema, COLUMN_KEY FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{}' and TABLE_SCHEMA = '{}'",
"""SELECT c.COLUMN_NAME,
 c.DATA_TYPE,
c.table_schema,
ksu.CONSTRAINT_NAME,
ksu.REFERENCED_TABLE_NAME,
ksu.REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ksu 
on c.TABLE_SCHEMA = ksu.TABLE_SCHEMA
and c.TABLE_NAME = ksu.TABLE_NAME
and c. COLUMN_NAME = ksu.COLUMN_NAME
WHERE c.table_name = '{}' and c.TABLE_SCHEMA = '{}'""",
        "GET_ALL_TABLE_NAMES": "SELECT table_schema, table_name FROM INFORMATION_SCHEMA.tables WHERE table_type='BASE TABLE' AND table_schema!='mysql' and table_schema!='performance_schema'",
        "GET_ALL_VIEWS_NAMES": "select table_schema, table_name from INFORMATION_SCHEMA.views WHERE table_schema!='sys' and table_schema!='mysql' and table_schema!='performance_schema'"
    }

    def __init__(self, loop, connection_string=None, **kwargs):
        super().__init__(loop, connection_string=connection_string, **kwargs)

        # self._columns_info = {}     # caching for system table
        self.system_fields = {
            # 'COLUMNS': ['column_name', 'udt_name'],
            'COLUMNS': ['name', 'type', 'schema', 'key', "ref_table", "ref column"],
        }
        self.system_field_names={
            'COLUMNS': ['name', 'type', 'schema'],
        }
        self.tables = None
        self.views = None

    @staticmethod
    def prep_statement_insert_update(table_name, column_names, primary_key):
        columns_string = ", ".join(column_names)
        primary_key = ", ".join(primary_key) if isinstance(primary_key, list) else primary_key
        update_string = f"""ON DUPLICATE KEY 
            DO UPDATE """
        for column_name in column_names:
            update_string += f"""SET {column_name} = EXCLUDED.{column_name}
                """
        a = "{}"
        prepared_statement = f"""INSERT INTO {table_name} ({columns_string})
            VALUES ({a}) ON DUPLICATE KEY DO UPDATE """
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
        list_for_update = []
        for i in enumerate(column_names):
            list_for_update.append(column_names[i]+" = "+values[i])
        update_string = ",\n".join(list_for_update)
        values_string = ", ".join(values)
        sql = self.prep_statement_insert_update(table_name,
                                                column_names,
                                                primary_key
                                                ).format(values_string)+update_string
        try:
            return await self.execute_sql(sql)
        except Exception as error:
            _logger.warning("Cannot execute SQL '{}'; Exception: {}".format(sql, error))
            return None

    async def _get_column_info(self, table_name, schema=None):
        schema_table_name = schema+'.'+table_name
        sql = self.sql_template("GET_COLUMN_INFO").format(table_name, schema)

        result = await self.execute_sql(sql)
        result_list = self.repack_as_dict(result, self.system_fields["COLUMNS"])
        _logger.debug("COLUMN INFO fot Table: '{}' {}".format(table_name, result_list))
        results = []
        field_names = []
        for each in result_list:
            if each["key"] == "PRIMARY":
                each["key"] = "PK"
            elif each["key"] == "FOREIGN":
                each["key"] = "FK"
            field_names.append(each["name"])
            results.append(each)
        self._columns_info[schema_table_name] = results
        return self._columns_info[schema_table_name], field_names

    async def _get_system_column_info(self, table_name="COLUMNS"):
        if not self._columns_info.get(table_name):
            fields = self.system_fields[table_name]
            fields_str = ",".join(fields)
            sql = self.sql_template("GET_SYSTEM_COLUMN_INFO").format(fields_str, table_name)

            result = await self.execute_sql(sql)
            result_list = self.repack_as_dict(result, fields)

            _logger.debug("SYSTEM COLUMN INFO fot Table: '{}' {}".format(table_name, result_list))

            self._columns_info[table_name] = result_list
        return self._columns_info[table_name]

    async def create_field_list(self,
                                fields: list = None,
                                schema='public',
                                table_name="",
                                **kwargs):

        model, field_names = await self.get_column_info(schema=schema, table_name=table_name)
        return model, field_names


    async def get_column_info(self, schema=None, table_name=None):
        return await self._get_column_info(schema=schema, table_name=table_name)
            # or await self._get_system_column_info(schema=schema, table_name=table_name)

    # todo inject OTHER elements - likes 'functions', 'types' etc
    async def get_catalog(self, **kwargs):
        tables = [{"name": row[1], "type": "table", "schema": row[0]} for row in await self.get_all_table_names()]
        views  = [{"name": row[1], "type": "view",  "schema": row[0]} for row in await self.get_all_views_names()]
        return tables + views

    async def get_all_table_names(self):
        data = await self.execute_sql(self.sql_template("GET_ALL_TABLE_NAMES"))
        # data1 = []
        # for row in data:
        #     schema_table = None
        #     if isinstance(row, tuple):
        #         schema_table = '.'.join(row)
        #     data1.append(schema_table or row)
        _logger.info(f"this is DATA: '{data}'")
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

        if not fields_list:
            fields_info = kwargs.get("fields_info") or await self.get_column_info(table_name)

            for each in fields_info:
                fields_list.append(each["name"])

        # todo - use PREPARE STATEMENT & BIND here
        fields_str = ", ".join(fields_list)
        sql = self.sql_template("SELECT").format(fields_str, table_name, limit, offset)

        return await self.execute_sql(sql)