import asyncio
import settings
from attrdict import AttrDict
from logging import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from .models import BASE, LocalDbModel, Adapter, Connector, User, ColumnView, View

from settings import PREDEFINED_ADAPTERS, PREDEFINED_CONNECTORS

_logger = getLogger(__name__)
EXAMPLE_TABLE_NAME = 'example_table'
EXAMPLE_STATUS = "test"


class ApplicationDbManagerBase:
    def __init__(self, connection):
        self.connection = connection
        self.session = None
        # self.last_result = {}

    def create_session(self):
        Session = sessionmaker(bind=self.connection)
        self.session = Session()
        _logger.info("Session Created")
        return self.session

    def _select_all(self, model) -> list:
        session = self.create_session()
        result = session.query(model).all()
        _logger.debug(f"Got from SQLite: '{result}'")
        return result

    def _get(self, model, key, value):
        session = self.create_session()
        obj = session.query(model).filter(key==value).first()
        return obj

    def _insert_record(self, model, *args, **kwargs):
        session = self.create_session()

        if kwargs:
            row = model(**kwargs)
            try:
                session.add(row)
                session.commit()
            except IntegrityError as e:
                _logger.warning("Cannot insert the {} record. Data: [{}]; Exception: {}".format(model, dict(**kwargs), type(e)))
                session.rollback()
                # session.merge(row)
                # session.commit()

    def add_predefined_tables(self, rows: list, model: BASE) -> None:
        """ Insert predefined data into the Model """
        for row in rows:
            try:
                self._insert_record(model, **row)
                _logger.debug("PREDEFINED Data Inserted for {}".format(model))
            except:
                _logger.warning("Cannot insert PREDEFINED Data into  {}. SKIPPED.".format(model))

    def setup_db(self):
        """ Insert predefined data """
        self.add_predefined_tables(PREDEFINED_ADAPTERS, Adapter)
        self.add_predefined_tables(PREDEFINED_CONNECTORS, Connector)

    def check_create_tables(self):
        """ Check SQLite tables...  Create them if it is required """
        engine = self.connection
        return LocalDbModel.metadata.create_all(engine)

    @classmethod
    def create_engine(cls):
        """ Creating Connection """
        engine = create_engine(f"sqlite:///{settings.DATABASE_ENVIRONMENT['NAME']}", echo=False)
        engine = cls(engine)
        engine.check_create_tables()
        _logger.info("Created ApplicationDbManager")
        engine.setup_db()
        return engine


class ApplicationDbManager(ApplicationDbManagerBase):
    def __init__(self, connection):
        super().__init__(connection)

    @staticmethod
    def as_obj(data: dict) -> object:
        return AttrDict(data)

    def insert(self, model, **kwargs):
        return self._insert_record(model, **kwargs)

    def allConnectors(self, *kwargs) -> list:
        return self._select_all(Connector)

    def allAdaptors(self, *kwargs) -> list:
        return self._select_all(Adapter)

    def allUsers(self):
        return self._select_all(User)

    def allViews(self):
        return self._select_all(View)

    def allColumnViews(self):
        return self._select_all(ColumnView)

    def insertConnector(self, **kwargs):
        return self._insert_record(Connector, **kwargs)

    def insertAdaptor(self, **kwargs):
        return self._insert_record(Adapter, **kwargs)

    def insert_ColumnView(self, **kwargs):
        return self._insert_record(ColumnView, **kwargs)

    def insert_View(self, **kwargs):
        return self._insert_record(View, **kwargs)

    def selectConnector(self, name):
        return self._get(Connector, Connector.name, name)

    def selectAdapter(self, name):
        return self._get(Adapter, Adapter.name, name)

    def selectView(self, name):
        return self._get(View, View.view, name)

    def selectColumnView(self, path_to_column):
        return self._get(ColumnView, ColumnView.path_to_column, path_to_column)
