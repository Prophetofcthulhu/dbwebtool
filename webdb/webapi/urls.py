import pathlib
#todo redis
from .view import test_page, adaptors, connectors, catalog, fetch_data, add_connectors, insert_update
from .websocket_dispatcher import ws_main_handler



import settings

PROJECT_ROOT = pathlib.Path(__file__).parent

static_follow_symlinks = True

route_handlers = [
    ##WEB Infrastructure
    {"route": "/", "action": "GET", "handler": test_page, "name": "test_page", "cors": settings.DEFAULT_CORS},

    {"route": '/static/',   "action": "STATIC",   "path": (PROJECT_ROOT / 'static'), "name": 'static',             'follow_symlinks' : static_follow_symlinks},
    {"route": '/assets/',   "action": "STATIC",   "path": (PROJECT_ROOT / 'assets'), "name": 'assets',             'follow_symlinks' : static_follow_symlinks},
    {"route": "/ws",        "action": "GET",      "handler": ws_main_handler},

    ## New Approach
    {"route": "/fetch/",          "action": "GET",    "handler": fetch_data,     "name": "fetch_data",     "cors": settings.DEFAULT_CORS},
    {"route": "/add_connectors/", "action": "GET",    "handler": add_connectors, "name": "add_connectors", "cors": settings.DEFAULT_CORS},
    {"route": "/adaptors/",       "action": "GET",    "handler": adaptors,       "name": "adaptors",       "cors": settings.DEFAULT_CORS},
    {"route": "/connectors/",     "action": "GET",    "handler": connectors,     "name": "connectors",     "cors": settings.DEFAULT_CORS},
    {"route": "/catalog/",        "action": "GET",    "handler": catalog,        "name": "catalog",        "cors": settings.DEFAULT_CORS},
    {"route": "/upsert/",        "action": "POST",    "handler": insert_update,  "name": "insert_update",  "cors": settings.DEFAULT_CORS},


    # Common 'Connections Infrastructure'
    {"route": "/create_connection/",     "action": "POST", "handler": create_connection, "name": "create_connection", "cors": settings.DEFAULT_CORS},
    {"route": "/get_connections/",       "action": "GET", "handler": get_connections, "name": "get_connections", "cors": settings.DEFAULT_CORS},
    # {"route": "/connections/", "action": "GET", "handler": connections, "name": "connections", "cors": settings.DEFAULT_CORS},


    ## todo REDIS - in PROGRESS
    {"route": "/redis/",                 "action": "GET",     "handler": redis_get_keys,         "name": "redis_get_all_keys", "cors": settings.DEFAULT_CORS},
    {"route": "/redis/",                 "action": "POST",    "handler": redis_get_velues,       "name": "redis_get_velues",   "cors": settings.DEFAULT_CORS}
    ]

