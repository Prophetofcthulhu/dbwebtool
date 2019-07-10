import aiohttp_jinja2
from aiohttp import web
from sysutils.web_utils import access_control_allow_origin_header
from sysutils.asynchronous.web.utils import async_input_entry
from sysutils.asynchronous.web.container_user_data import AsyncRequestData
from sysutils.utils.debug import nice_print
from sysutils.utils.json_tools import json_dumps_extended
from sysutils.utils.dict_utils import safeget, multikey_sort
from core.utils import repack_as_dict
from data_adapter.adaptor_factory import AdaptorFactory
from logging import getLogger

import settings

_logger = getLogger(__name__)


#todo Moove into the same COMMON module
def json_response(data: (dict, list)):
    json = json_dumps_extended(data)

    return web.Response(text=json,
                        status=200,
                        content_type='application/json',
                        headers=access_control_allow_origin_header())


# todo - SHOULD BE REMOVED & or SO
@aiohttp_jinja2.template('test_page.html')
async def test_page(request):
    _logger.debug("test page invoking")
    return {"test_id": "000000"}


async def get_table_data(adapter, table, schema=None, limit=-1, offset=0):
    data, meta = await adapter.fetch(table_name=table, schema=schema, limit=limit, offset=offset)
    model = safeget(meta, "model")
    names = [safeget(each, "name") for each in model]
    if data and names:
        data = repack_as_dict(data, names)
    else:
        data = {}
        meta["model"] = []

    return {"data": data, "meta": {"limit": limit, "table": table, **meta}}


# todo refactor response
async def get_table_meta_data(adaptor):
    return {"data": await adaptor.get_catalog()}


async def expand_data(adapter, data):
    if data:
        for item in data:
            if item.get("type") in ("table", "view"):
                item["count"] = await adapter.count_items(item.get("name"), item.get("schema"))
    return data

@async_input_entry
async def connectors(request):
    app = request.app
    dbmanager = app[settings.DB_PROPERTY_NAME]
    inited_connectors = app[settings.PROPERTY_DATA_CONNECTORS]

    def presentation_view(connector):
        item = {}
        name = connector.name
        adapter = inited_connectors.get(name)
        if adapter:
            item["status"] = "readonly" if connector.read_only else "active"
            item["connection"] = adapter.safe_connection_string
            item["ping_time"] = adapter.ping_time
        else:
            item["status"] = "error"
            item["ping_time"] = 0
            # todo Implemente "safe_connection" for "error" connectors
            item["connection"] = "***"
        item["driver"] = connector.type.name
        item["name"] = name
        item["title"] = name
        return item

    data = [presentation_view(connector) for connector in dbmanager.allConnectors()]
    return json_response(data)


@async_input_entry
async def adaptors(request):
    app = request.app
    dbmanager = app[settings.DB_PROPERTY_NAME]

    # todo Inject Info about CURRENT connections for this Adapter
    inited_connectors = app[settings.PROPERTY_DATA_CONNECTORS]

    data = [adaptor.as_dict() for adaptor in dbmanager.allAdaptors()]
    return json_response(data)


SHOW_TABLES = "__tables__"


async def do_fetch_data(adapter, connector, table, schema, limit=-1, offset=0):
    status = "OK"
    if not adapter:
        _logger.warning("Cannot load Adapter for Connector: '{}'".format(connector))
        status = "ERROR"
        data = {"message": "Unknown connector '{}'".format(connector)}
    else:
        if table == SHOW_TABLES:
            data = await get_table_meta_data(adapter)
        else:
            data = await get_table_data(adapter, table, schema, limit, offset)
        if data and data.get("data") is None:
            status = "ERROR"
            data = {"message": "Cannot fetch data from '{}.{}' for connector '{}'".format(table, schema, connector)}
    return status, data


async def insert_update_data(adapter,
                             connector,
                             table: str,
                             schema: str or None,
                             primary_key: list or None,
                             columns: list,
                             values: list,
                             ):
    status = "OK"
    if not adapter:
        _logger.warning("Cannot load Adapter for Connector: '{}'".format(connector))
        status = "ERROR"
        data = {"message": "Unknown connector '{}'".format(connector)}
    else:
        data = await adapter.execute_insert_update(table_name=table,
                                                   schema=schema,
                                                   primary_key=primary_key,
                                                   column_names=columns,
                                                   values=values,
                                                   )
        if data and data.get("data") is None:
            status = "ERROR"
            data = {"message": "Cannot fetch data from '{}.{}' for connector '{}'".format(table, schema, connector)}
    return status, data


@async_input_entry
async def catalog(request):
    app = request.app
    connectors = app[settings.PROPERTY_DATA_CONNECTORS]
    controller = AsyncRequestData(request)
    connector = await controller.get_param('connector')
    mode =      await controller.get_param('mode')
    schema =    await controller.get_param('schema', "public")
    dbname =    await controller.get_param('dbname', "")
    adapter = connectors.get(connector)

    status, data = await do_fetch_data(adapter, connector, SHOW_TABLES, "")

    data = data.get("data")
    if mode == "expand":
        data = await expand_data(adapter, data)
        data = multikey_sort(data, ['schema', 'type', 'name'], can_be_skipped={'schema'})
    else:
        data = multikey_sort(data, ['type', 'name'])
    return json_response(data)


@async_input_entry
async def insert_update(request):
    app = request.app
    connectors = app[settings.PROPERTY_DATA_CONNECTORS]
    controller = AsyncRequestData(request)
    connector = await controller.get_param('connector')
    adapter = connectors.get(connector)

    table =         await controller.get_param('table', "retards")
    schema =        await controller.get_param('schema', "test_db")
    columns =       await controller.get_param('columns', [])
    primary_key =   await controller.get_param('primary_key', [])
    values =        await controller.get_param('values', [])

    status, data = await insert_update_data(adapter,
                                            connector,
                                            table=table,
                                            schema=schema,
                                            primary_key=primary_key,
                                            columns=columns,
                                            values=values,
                                            )
    # nice_print(data)
    return json_response(data)


# todo FIX for COMPLEX Types (use custom JSON Serialiser)
@async_input_entry
async def fetch_data(request):
    app = request.app
    connectors = app[settings.PROPERTY_DATA_CONNECTORS]
    controller = AsyncRequestData(request)
    connector = await controller.get_param('connector')
    adapter = connectors.get(connector)

    table = await controller.get_param('table', SHOW_TABLES)
    schema = await controller.get_param('schema', None)
    limit = await controller.get_param('limit', 10000)
    offset = await controller.get_param('offset', 0)

    status, data = await do_fetch_data(adapter, connector, table=table, schema=schema, limit=limit, offset=offset)
    return json_response(data)


# @async_input_entry
# async def create_table(request):
#     app = request.app
#     connectors = app[settings.PROPERTY_DATA_CONNECTORS]
#     controller = AsyncRequestData(request)
#     connector = await controller.get_param('connector')
#     adapter = connectors.get(connector)
#
#     table = await controller.get_param('table', SHOW_TABLES)
#     schema = await controller.get_param('schema', "")
#
#     # nice_print(data)
#     return json_response(data)

@async_input_entry
async def add_connectors(request):
    app = request.app
    connectors = app[settings.PROPERTY_DATA_CONNECTORS]
    controller = AsyncRequestData(request)
    system_db = app[settings.DB_PROPERTY_NAME]

    name =      await controller.get_param('name')
    con_type =  await controller.get_param('type')
    host =      await controller.get_param('host')
    port =      await controller.get_param('port', None)
    user =      await controller.get_param('user', None)
    password =  await controller.get_param('password', None)
    dbname =    await controller.get_param('dbname', None)
    read_only = await controller.get_param('read_only', 1)

    read_only = bool(read_only)

    if connectors.get(name):
        return json_response({"status": "ERROR",
                              "message": "Connection already exists"})

    try:
        adapter = system_db.selectAdapter(con_type)
        adaptor = AdaptorFactory.get_adaptor(adapter)
        connection_string = adaptor.compile_connection_string(dbname=dbname,
                                                              host=host,
                                                              port=port,
                                                              user=user,
                                                              password=password)

        system_db.insertConnector(
            type_id=adapter.id,
            name=name,
            connection=connection_string,
            read_only=read_only
        )
        return json_response({"status": "OK"})
    except Exception as e:
        _logger.error(f"Could not create '{name}'.  Exception: '{e}'")
        return json_response(
            {"status" : "ERROR",
             "message": e}
        )
