import re
import logging
# from cassandra.util import OrderedMapSerializedKey, SortedSet
from cassandra.cluster import NoHostAvailable
from sysutils.asynchronous.broker.cassandra.cassandra_broker import CassandraBroker
# from sysutils.debug import nice_print
from webdb.data_adapter.base_abstract_adaptor.base_adaptor import DatabaseAbstractAdaptor
from .json_dumper import json_dumps


_logger = logging.getLogger(__name__)


class CassandraAdapterBase(DatabaseAbstractAdaptor):
    DEFAULT_PORT = 9042
    DEFAULT_NODES = ["127.0.0.1"]
    DEFAULT_CONNECTION_STRING = "nodes=193.24.30.63 port=9042"
    CHECK_CONNECTION_TIMEOUT = 4
    COUNT_ITEM_TIMEOUT = 10

    def __init__(self, loop, connection_string=None, **kwargs):
        if connection_string:
            nodes, port, user, password = self.unpack_connection_string(connection_string)
            self._connection_string = connection_string
        else:
            nodes = kwargs.pop("nodes", None) or self.DEFAULT_NODES
            port = kwargs.pop("port", None) or self.DEFAULT_PORT
            user = kwargs.pop("user", None)
            password = kwargs.pop("password", None)
            self._connection_string = self.compile_connection_string(nodes, port, user, password)

        self._nodes = nodes
        self._port = port
        self._user = user
        self._password = password
        self._broker = None

        super().__init__(loop,  connection_string=self._connection_string)

    @staticmethod
    def compile_connection_string(host, port, user=None, password=None):
        connection_string = "nodes="+str(host)+" port="+str(port)
        if user:
            connection_string += f" user={user}"
        if password:
            connection_string += f" password={password}"
        return connection_string


    @classmethod
    def unpack_connection_string(cls, connection_string: str):
        nodes_regex = r"(?<=nodes=)[a-zA-Z0-9.\[\],]*"
        port_regex = r"(?<=port=)[a-zA-Z0-9._\-]*"
        password_regex = r'(?<=password=)[a-zA-Z0-9.\[\],!@#$%^&*()_\-+=|\\]*'
        user_regex = r'(?<=name=)[a-zA-Z0-9.]*'

        nodes = re.search(nodes_regex, connection_string)
        port = re.search(port_regex, connection_string)
        password = re.match(password_regex, connection_string)
        user = re.match(user_regex, connection_string)

        nodes = nodes.group(0) if nodes else cls.DEFAULT_NODES
        port = port.group(0) if port else cls.DEFAULT_PORT
        password = password.group(0) if password else None
        user = user.group(0) if user else None

        if nodes[0] == "[":
            nodes = nodes[1:-1]
            nodes = nodes.split(",")
        return nodes, port, user, password

    @classmethod
    def clear_connection_string(cls, connection_string):
        return connection_string

    @property
    def broker(self):
        if not self._broker:
            self._broker = CassandraBroker(
                loop=self._loop,
                nodes=self._nodes,
                port=self._port)
            self._broker.do_connect()
        return self._broker

    async def create_conn(self):
        return self.broker

    @property
    def port(self):
        return str(self._port)

    @property
    def nodes(self):
        return list(self._nodes)

    async def execute_select(self, query_string: str, **kwargs) -> list:
        try:
            _logger.debug("Executing '{}'...".format(query_string))
            conn = await self.create_conn()
            return await conn.execute_select(query_string)
        except NoHostAvailable:
            _logger.warning("Cannot perform request '{}'; NoHostAvailable".format(query_string))
            return []
        except Exception as ex:
            _logger.warning("Cannot perform request '{}'; Exception: {}".format(query_string, ex))
            raise

    @staticmethod
    def prepare_query_string(query_string):
        return query_string.strip()

    @staticmethod
    async def post_process(data):
        return data

    @staticmethod
    def json_dumps(data, **kwargs):
        return json_dumps(data, **kwargs)

    async def create_table_model(self, table_name, model, cql=""):
        try:
            if not self.read_only:
                if not cql:
                    cql = self.cql_for_create_table(table_name, model)
                conn = await self.create_conn()
                await conn.execute_wait_result(cql)
            else:
                _logger.info("Read only connection. Create table '{}'  SKIPPED".format(table_name))
        except Exception as error:
            _logger.warning("Cannot create Table '{}'. Exception: {}".format(table_name, error))

    async def execute_insert_update(self,
                                    table_name: str,
                                    column_names: list,
                                    values: list,
                                    schema: list or None = None,
                                    primary_key=None,
                                    *args, **kwargs):
        raise NotImplemented("execute_insert_update")

    async def insert(self, table_name, columns, data, keyspace=None):
        if self.read_only:
            _logger.error("Connection is read_only")
            return "Connection is read_only"
        if not keyspace:
            table_name = keyspace+"."+table_name
        conn = await self.create_conn()
        return await conn.insert_record(table_name=table_name, columns=columns, data=data)

    @staticmethod
    def cql_for_create_table(table_name, table_params_fields: list, ifnotexist=True) -> str:
        exist = " IF NOT EXISTS" if ifnotexist else ''
        cql_base = "CREATE TABLE{} {} ".format(exist, table_name)
        cql_list = []
        pk_list = []
        for item in table_params_fields:
            cql_piece = "{} {} ".format(item["name"], item["type"])
            if item.get("PK"):
                pk_list.append(item["name"])
            cql_list.append(cql_piece)
        cql_pieces = ", ".join(cql_list)

        pk_string = ", PRIMARY KEY ("+", ".join(pk_list)+")" if pk_list else ""
        cql = cql_base + '( ' + cql_pieces + pk_string + ')'
        return cql

    @staticmethod
    def is_read_only_request(sql):
        regex = '^(select|pragma).*$'
        result = re.search(regex, sql.lower())
        return result

    async def execute_cql(self, cql):
        if self.read_only and not self.is_read_only_request(cql):
            conn = await self.create_conn()
            await conn.execute_wait_result(cql)

    async def update(self, table_name, columns, data, keyspace=""):
        pass
