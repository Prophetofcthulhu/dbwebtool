import traceback
import asyncio
import settings
from logging import getLogger
from webdb.data_adapter.adaptor_factory import ConnectorFactory

_logger = getLogger(__name__)
EXAMPLE_TABLE_NAME = 'example_table'
EXAMPLE_STATUS = "test"


# async def _start_connector(connectors, app):


async def _start_connectors_all(connectors, app):
    loop = app.loop
    adapters = app[settings.PROPERTY_DATA_ADAPTERS]
    connector_cache = app[settings.PROPERTY_DATA_CONNECTORS]

    reconnected = []

    for connector in connectors:
        try:
            adaptor = ConnectorFactory.get_connector(loop, connector)
            if adaptor:
                # todo - do this asynchronically
                timeping = await adaptor.ping()
                _logger.info("Load Adaptor '{}' as '{}' for '{}'; ping: {}".format(
                    connector.type,
                    adaptor.safe_connection_string,
                    connector,
                    timeping)
                )
                connector_cache[connector.uid] = adaptor
                adapters[connector.uid] = adaptor
                reconnected.append(connector.uid)
            else:
                _logger.info("Cannot load Adaptor '{}'  for '{}'. SKIPPED".format(connector.type, connector))
        except Exception as ex:
            _logger.error("Cannot load Adapter for {}. Exception: {}. {}; SKIPPED.".format(connector.type, ex, traceback.format_exc()))

        # Postgres already Implemented
        # Please IMPLEMENT Cassandra using CODE below

        #     adapter = CassandraDataAdapter(loop, port, nodes)
        #     adapters["Cassandra"] = adapter
        # elif db_type == "Cassandra":
        #     from data_adapter.cassandra.adapter import CassandraDataAdapter
        #     conn_name = row["name"]
        #     connection = json_loads(row["connection"])
        #     port = connection["port"]
        #     nodes = connection["nodes"]
        #     adapter = CassandraDataAdapter(loop, port, nodes)
        #     if not adapters.get("Cassandra"):
        #         adapters["Cassandra"] = {}
        #     adapters["Cassandra"][conn_name] = adapter
        #     _logger.info("Start of Cassandra '{}' adaptor was {}".format(conn_name, "a SUCCESS" if adapters["Cassandra"][conn_name] else "an ERROR"))
        # else:
        #     db_type = row['type']
        #     _logger.error(f"'{db_type}' is not implemented")
    _logger.info("Registered Connections reconnected: {}".format(reconnected))


def check_start_connectors(connectors, app):
    asyncio.ensure_future(_start_connectors_all(connectors, app), loop=app.loop)

