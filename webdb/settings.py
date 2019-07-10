import os, logging, socket
from os import environ
from os.path import isfile

environ['ENVIRONMENT_MODE'] = environ.get('ENVIRONMENT_MODE', '').lower() or 'develop'

try:
    from envparse import env
    if isfile('.env'):
        env.read_envfile('.env')
except:
    pass

APPLICATION_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SERVICE_NAME = "WebDBTool"
HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_HOST = environ.get('HOST') or socket.gethostname()
HOST_NAME = os.uname().nodename

VERBOSE = bool(__debug__)

LOOP = "asyncio"
TEMPLATE_ENGINE = "JINJA2"


WEBSERVER_TEMPLATE_FOLDER = [
    "{}/webapi/templates".format(APPLICATION_BASE_DIR)
]

DATA_ADAPTER_TEMPLATE_ROOT = "{}/webapi/templates/data_adapter".format(APPLICATION_BASE_DIR)

WEBSYS_TEMPLATE_PARAMETERS = {
    #"WEBSOCKET_URL": 'ws://172.16.0.139:8090/ws'
}

# http configure
import aiohttp_cors
DEFAULT_CORS = {
    "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*"),
    # "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers=["Access-Control-Allow-Origin", "*"], allow_headers="*"),
}


DATABASE_ENVIRONMENT = {
        'ENGINE': 'aiosqlite',
        'NAME': os.path.join("../db/", 'db.sqlite3'),
    }


DB_PROPERTY_NAME = "application_db"
PROPERTY_DATA_ADAPTERS = "data_adapters"
PROPERTY_DATA_CONNECTORS = "data_connectors"

ADAPTORS_TABLE_NAME = "adaptors"
CONNECTIONS_TABLE_NAME = "connections"
USERS_TABLE_NAME = "users"
GROUPS_TABLE_NAME = "groups"
ColumnView_TABLE_NAME = "column_view"

PREDEFINED_ADAPTERS = [
    {"name": "Postgres",    "driver": "webdb.data_adapter.postgre.base_adaptor.PostgreSQLAdaptor"},
    {"name": "SQLite",      "driver": "webdb.data_adapter.sqlite.base_adaptor.SqliteBaseAdaptor"},
    {"name": "Cassandra",   "driver": "webdb.data_adapter.cassandra.adapter.CassandraDataAdapter"},
    {"name": "MySQL",       "driver": "webdb.data_adapter.mysql.base_adaptor.MySQLAdaptor"},
]

PREDEFINED_CONNECTORS = [
    {"name": "PostgresDemoTest", "type_id": 1, "connection": 'dbname=test_db user=**** password=**** host=192.168.0.105 port=54832', "read_only": False},
    {"name": "SQLiteThisDB",     "type_id": 2, "connection": DATABASE_ENVIRONMENT["NAME"], "read_only": True},
    {"name": "CassandraTest",    "type_id": 3, "connection": 'nodes=[193.24.30.63] port=9042', "read_only": False},
    # {"name": "CassandraTest", "type_id": 3, "connection": '{ "nodes": ["193.24.30.63"], "port": 9042 }', "read_only": False},
    {"name": "MySQLTest",        "type_id": 4, "connection": 'db=public user=root password=**** host=193.24.30.63 port=6603', "read_only": False},
    # {"name": "CassandraTest", "type_id": 3, "connection": '{ "nodes": ["192.168.0.105"], "port": 9042 }', "read_only": False},
   {"name": "Worddict", "type_id": 1, "connection": 'dbname=worddict_db user=worddictadmin password=worddict_admin host=127.0.0.1 port=54832', "read_only": True}
]


# logging configure
class UDPLogFilter(logging.Filter):
    def filter(self, rec):
        rec.hostname = HOST_NAME
        rec.servicename = SERVICE_NAME
        return True


from logging.config import dictConfig
from settings_logging import LOGGING
dictConfig(LOGGING)

try:
    from local_settings import *
    print("*** ATTENTION! LOCAL SETTINGS LOAD ***")
except ImportError:
    pass
