from logging import getLogger

from sysutils.utils.reflection_utils import class_by_name
from core.models import Connector, Adapter
from .base_abstract_adaptor.base_adaptor import DatabaseAbstractAdaptor


_logger = getLogger(__name__)


class AdaptorFactory:
    @staticmethod
    def get_adaptor(adapter: Adapter) -> DatabaseAbstractAdaptor:
        driver_class_name = adapter.driver
        return class_by_name(driver_class_name)


class ConnectorFactory:
    @staticmethod
    def get_connector(loop, connector: Connector) -> DatabaseAbstractAdaptor:
        adapter = connector.type
        # driver_class_name = adapter.driver
        # driver_class = class_by_name(driver_class_name)
        driver_class = AdaptorFactory.get_adaptor(adapter)
        adapters = driver_class(loop, connector.connection)
        _logger.info("Adaptor '{}' INITED for CONNECTOR: {}".format(adapter.driver, connector))
        return adapters

