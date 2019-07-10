from logging import getLogger
_logger = getLogger(__name__)

from .base_adaptor import DatabaseAbstractAdaptor


class DatabaseAbstractNoSQLAdaptor(DatabaseAbstractAdaptor):
    pass