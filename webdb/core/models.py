from attrdict import AttrDict
from sqlalchemy import table, column, Column, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import INTEGER, TEXT, Boolean, String
from sqlalchemy.orm import mapper, relationship
from sqlalchemy.ext.declarative import declarative_base
from sysutils.utils.object_utils import obj_as_dict
from settings import ADAPTORS_TABLE_NAME, CONNECTIONS_TABLE_NAME, USERS_TABLE_NAME, GROUPS_TABLE_NAME, ColumnView_TABLE_NAME

BASE = declarative_base()


class LocalDbModel(BASE):
    __abstract__ = True

    @classmethod
    def model_name(cls):
        return cls.__name__


class AsDictMixin:
    def as_dict(self):
        return obj_as_dict(self, self.PRESENTATIVE_FIELDS, transformer=lambda x: str(x))

    def as_obj(self, data=None):
        return AttrDict(data or self.as_dict())


class Adapter(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["id", "name", "driver"]
    __tablename__ = ADAPTORS_TABLE_NAME
    id = Column("id", INTEGER, primary_key=True)
    name = Column("name", String(128))
    driver = Column("driver", String(512))

    def __str__(self):
        return self.name


class Connector(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["name", "type", "connection", "read_only"]
    __tablename__ = CONNECTIONS_TABLE_NAME
    # id = Column("id", INTEGER, primary_key=True)  # Auto-increment should be default
    name = Column("name", TEXT, primary_key=True)
    type_id = Column("type_id", ForeignKey(Adapter.id))
    type = relationship(Adapter, backref="connectors")
    connection = Column("connection", TEXT)
    read_only = Column("read_only", Boolean)

    @property
    def uid(self):
        return "{}{}".format(self.name, "")

    def __str__(self):
        return self.name


class User(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["id", "name"]
    __tablename__ = USERS_TABLE_NAME
    id = Column("id", INTEGER, primary_key=True)
    name = Column("name", String(50))


class Group(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["id", "name"]
    __tablename__ = GROUPS_TABLE_NAME
    id = Column("id", INTEGER, primary_key=True)
    name = Column("name", String(50))


class View(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["id", "view"]
    __tablename__ = "view"
    id = Column("id", INTEGER, primary_key=True)
    view = Column("view", String(50))


class ColumnView(LocalDbModel, AsDictMixin):
    PRESENTATIVE_FIELDS = ["id", "path_to_column", "view_id", "view"]
    __tablename__ = ColumnView_TABLE_NAME
    id = Column("id", INTEGER, primary_key=True)
    path_to_column = Column("path_to_column", String(), unique=True)
    view_id = Column("view_id", ForeignKey(View.id))
    view = relationship(View, backref="column_view")

