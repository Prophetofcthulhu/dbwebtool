#!/usr/bin/env python

import logging
import asyncio
import signal
import traceback
import settings

from sysutils.asynchronous.system_loop import get_main_loop
from sysutils.asynchronous.web.web_server import start_web_server
from core.app_db_manager import ApplicationDbManager
from settings import SERVICE_NAME
from webapi.urls import route_handlers


_logger = logging.getLogger(__name__)


def close_app(*args, **kwargs):
    _logger.info("Service {} Stopped".format(SERVICE_NAME))
    pass


def shutdown_handler(loop):
    _logger.info("Stopping Service {}...".format(SERVICE_NAME))
    tasks = asyncio.Task.all_tasks(loop)
    try:
        loop.stop()
        for t in tasks:
            t.cancel()
    except Exception as ex:
        _logger.debug("Exception during stopping service: {}; {}".format(ex, traceback.format_exc()))
        pass


async def empty_middleware(app, handler):
    async def middleware_handler(request):
        return await handler(request)
    return middleware_handler


def check_load_connectors(app, db_engine):
    from core.connection_manager import check_start_connectors
    connectors = db_engine.allConnectors()

    if connectors:
        check_start_connectors(connectors, app)
        _logger.info("I got adapters from SQLite [{}]".format(connectors))
    else:
        _logger.warning("No info for connections")


def db_init(app):
    db_property_name = settings.DB_PROPERTY_NAME
    db_engine = ApplicationDbManager.create_engine()
    app[db_property_name] = db_engine
    app[settings.PROPERTY_DATA_ADAPTERS] = {}
    app[settings.PROPERTY_DATA_CONNECTORS] = {}
    check_load_connectors(app, db_engine)


def go(host='0.0.0.0', port=7080, handlers=route_handlers):
    loop = get_main_loop("asyncio")

    loop.add_signal_handler(signal.SIGINT, shutdown_handler, loop)

    tasks = ()
    middlewares = []

    def web_setup(app):
        db_init(app)

    start_web_server(loop,
                     host=host,
                     port=port,
                     handlers=handlers,
                     tasks=tasks,
                     setup_app=web_setup,
                     close_app=close_app,
                     settings=settings,
                     middlewares=middlewares)

    _logger.info("SERVICE '{}' stopped".format(settings.SERVICE_NAME))


if __name__ == "__main__":
    go(host="0.0.0.0", port=7080)
