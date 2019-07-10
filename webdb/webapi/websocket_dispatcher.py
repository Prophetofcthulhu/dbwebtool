import traceback
import time
import json
import logging
import uuid
import asyncio
import aiohttp
from aiohttp import web
from aiohttp.web import json_response

from attrdict import AttrDict
from sysutils.utils.debug import nice_format

from sysutils.asynchronous.utils import minisleep
from sysutils.asynchronous.exception_handler import cycling_and_ignore_exception

import settings

from aiohttp.http_websocket import WSMessage    # for investigation


from logging import getLogger
_logger = getLogger(__name__)


async def ws_main_handler(request):
    """
    Perform ALL WS Requests
    :param request:
    :return:
    """

    db_manager = request.app[settings.DB_PROPERTY_NAME]
    loop = request.app.loop
    current_user_id = request.query.get('user') or ""

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    try:
        async for msg in ws:
            _logger.debug("######## MSG: {} {} type:[{}]".format(type(msg), msg, msg.type))
            if msg.type == aiohttp.WSMsgType.TEXT:
                data_str = getattr(msg, 'data', '').strip()
                if len(data_str) > 0:
                    if msg.data == 'heartbeat':
                        await ws.send_str('heartbeat')
                    else:
                        try:
                            event = json.loads(data_str)
                        except Exception as e:
                            _logger.error("NOT JSON: '{}'. {}; {}".format(data_str, e, traceback.format_exc()))
                            continue
                        else:
                            _logger.debug("#### GOT MESSAGE '{}'; Processing it...".format(event))
                            _logger.debug("PERFORM WEB SOCKET MESSAGE")
                else:
                    _logger.warning("Empty WS request")
                    pass

    except asyncio.CancelledError:
        _logger.info("WS Disconnected")
    except Exception as e:
        _logger.error("****** Exception: {}; {} ".format(e, traceback.format_exc()))
        pass
    finally:
        _logger.info("WS Closed")

    return ws
