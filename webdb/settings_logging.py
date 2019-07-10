import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"base dir: {BASE_DIR}")

LOGGING = {
        'version': 1,
        'formatters': {
            'normal': {
                'format': '%(asctime)s %(levelname)-8s %(name)-10s %(message)s',
                'datefmt' : "%Y-%m-%d %H:%M:%S"
            },
            'verbose': {
                'format': '%(asctime)s %(levelname)-8s %(module)s::%(name)-10s %(message)s (%(filename)s:%(lineno)d).',
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
            'debug': {
                'format': '%(asctime)s %(levelname)-8s %(filename)16s:%(lineno)-4d :: %(message)s',
                'datefmt' : "%H:%M:%S"
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
            'only_message': {
                'format': '%(message)s',
            },
        },
        'disable_existing_loggers': False,
        # 'filters': {
        #     'require_debug_false': {
        #         '()': 'django.utils.log.RequireDebugFalse'
        #     },
        # },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
                },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/application_main.log'.format(BASE_DIR),
                'maxBytes': 1024*1024*1,
                'backupCount': 10,
                'formatter': 'verbose'
                },
        },
        'root': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'loggers': {
            'runtime': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    }

