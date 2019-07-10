import settings
from logging import getLogger
from data_adapter.cassandra.json_dumper import json_dumps
from aiohttp.web import json_response
from webapi.views.postgre import get_postgre_adapter, get_all_tables
from webapi.views.cassandra import get_cassandra_adapter


_logger = getLogger(__name__)


async def create_connection(request):
    app = request.app
    post_body = await request.post()
    conn_name = post_body.get("name") or "Postgre1"
    conn_type = post_body.get("type") or "PostgreSQL"
    adapters = app[settings.PROPERTY_DATA_ADAPTERS]
    connectors = app[settings.PROPERTY_DATA_CONNECTORS]

    if not adapters.get(conn_type):
        adapters[conn_type] = {}
    adapter = adapters[conn_type].get(conn_name)
    if adapter:
        return json_response({"responce": "Connection with this name already exists"}, dumps=json_dumps)
    if conn_type == "PostgreSQL":
        await get_all_tables(request)
        data = {"responce": "Connection Created"}
    elif conn_type == "cassandra":
        await get_cassandra_adapter(request)
        data = {"responce": "Connection Created"}
    else:
        data = {"responce": "This DB is not implemented"}
    return json_response(data, dumps=json_dumps)


# def get_connections(request):
#     app = request.app
#     adapters = app[settings.PROPERTY_DATA_ADAPTERS]
#     result = []
#     for adapter_type in adapters:
#         if adapter_type == "PostgreSQL":
#             for name in adapters[adapter_type]:
#                 _logger.info(f"Supposed to be a name of adaptor  '{name}'")
#                 status = "active"
#                 if adapters[adapter_type][name].read_only:
#                     status = "readonly"
#                 address = adapters[adapter_type][name].dsn
#                 adapter = {
#                     "title": name,
#                     "status": status,
#                     "type": adapter_type,
#                     "address": address
#                 }
#                 result.append(adapter)
#         if adapter_type == "Cassandra":
#             for name in adapters[adapter_type]:
#                 _logger.info(f"Supposed to be a name of adaptor  '{name}'")
#                 status = "active"
#                 if adapters[adapter_type][name].read_only:
#                     status = "readonly"
#                 address = "port: "+str(adapters[adapter_type][name].port)+"nodes:"+str(adapters[adapter_type][name].nodes)
#                 adapter = {
#                     "title": name,
#                     "status": status,
#                     "type": adapter_type,
#                     "address": address
#                 }
#                 result.append(adapter)
#
#     print(adapters)
#     print(result)
#     data = {"result": result}
#     return json_response(data, dumps=json_dumps)