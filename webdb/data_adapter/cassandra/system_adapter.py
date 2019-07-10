"""
see https://docs.datastax.com/en/cql/3.3/cql/cql_using/useQuerySystem.html
"""

import logging
import async_timeout
from sysutils.debug import nice_print
from sysutils.utils.timer import Timer
from .base_adapter import CassandraAdapterBase


_logger = logging.getLogger(__name__)


class CassandraSystemDataAdapter(CassandraAdapterBase):
    def __init__(self, loop, connection_string=None, port=None, nodes=None):
        super().__init__(loop, connection_string=connection_string, port=port, nodes=nodes)
        self._columns_info = {}

        self.system_fields = {
            'types':        ['keyspace_name', 'type_name', 'field_names', 'field_types'],
            'triggers':     ['keyspace_name', 'table_name', 'trigger_name', 'options'],
            'indexes':      ['keyspace_name', 'table_name', 'index_name', 'kind', 'options'],
            'aggregates':   ['keyspace_name', 'aggregate_name', 'argument_types', 'final_func', 'initcond', 'return_type', 'state_func', 'state_type'],
            'columns':      ['keyspace_name', 'table_name', 'column_name', 'clustering_order', 'column_name_bytes', 'kind', 'position', 'type'],
            'views':        ["TBD", 'https://docs.datastax.com/en/cql/3.3/cql/cql_using/useQuerySystem.html'],
        }

    async def ping(self) -> int:
        """ Check if database online & available for connection """
        try:
            with Timer() as timer:
                with async_timeout.timeout(self.CHECK_CONNECTION_TIMEOUT):
                    await self.system_types()
            self._ping_time = timer.elapsed()
            return self._ping_time

        except Exception as ex:
            _logger.info("Ping failure in timeout {} sec.".format(self.CHECK_CONNECTION_TIMEOUT))
            return -1

    def whole_table_name(self, table_name: str, keyspace_name:str) -> str:
        return "{}.{}".format(keyspace_name, table_name).lower()

    def schema_query_string(self, table_name: str, fields: list) -> str:
        selector = ", ".join(fields)
        return "SELECT {} FROM system_schema.{}".format(selector, table_name)

    async def sys_table_data(self, table_name: str = None) -> {}:
        fields = self.system_fields[table_name]
        rows = await self.execute_select(self.schema_query_string(table_name, fields))
        result = self.repack_as_dict(rows, fields)
        return result

    def _unpack_columns(self, columns):
        info = self._columns_info

        for col in columns:
            tabname = self.whole_table_name(col['table_name'], col['keyspace_name'])
            if not tabname in info:
                info[tabname] = []
            info[tabname].append({col['column_name']: col})

    async def load_all_columns_info(self):
        if not self._columns_info:
            data = await self.system_columns()
            self._unpack_columns(data)
        return self._columns_info

    async def get_column_info(self, table_name, keyspace_name=None):
        tabname = self.whole_table_name(table_name, keyspace_name).lower()
        columns_info = await self.load_all_columns_info()
        info = columns_info.get(tabname)
        info = self.sort_info_by_positions(info)
        fields, model = [], []
        for each in info:
            column_info = {
                    "name": each['column_name'],
                    "type": each['type'],
                    "key": "PK" if each['kind'] == "partition_key" else ""
                }
            model.append(column_info)
            fields.append(each['column_name'])
        return model, fields

    async def system_types(self) -> []:
        return await self.sys_table_data('types')

    async def system_indexes(self) -> []:
        return await self.sys_table_data('indexes')

    async def system_columns(self) -> []:
        return await self.sys_table_data('columns')

    async def system_triggers(self) -> []:
        return await self.sys_table_data('triggers')

    @staticmethod
    def sort_info_by_positions(columns_info):
        """
        Repack Column info taking in account 'kind/position'
        against just regular order in "Result"
        :param columns_info: <list of dicts> columns info
        :return: [list of dicts] - Order of Items are ony updated
        """
        ordered_by = {
            'partition_key': [],
            'clustering': [],
            'regular': [],
        }
        result = []
        for col in columns_info:
            col_name = list(col.keys())[0]
            col_data = col[col_name]
            kind = col_data['kind']
            ordered_by[kind].append(col_data)

        for name in ["partition_key", "clustering", "regular"]:
            cols = ordered_by[name]
            result.extend(sorted(cols, key=lambda x: int(x['position'])))

        return result

    async def get_catalog(self):
        columns_info = await self.load_all_columns_info()
        result = []
        for tabname in columns_info:
            schema, name = tabname.split(".")
            result.append({"name": name, "type": "table", "schema": schema})
        nice_print(result)
        return result

    async def count_items(self, table_name, schema=""):
        try:
            with async_timeout.timeout(self.COUNT_ITEM_TIMEOUT):
                name = "{}.{}".format(schema, table_name) if schema else table_name
                cql = "SELECT count(*) from {}".format(name)
                row = await self.execute_select(cql)
                count = row[0][0]
                return count

        except Exception as ex:
            _logger.info("Ping failure in timeout {} sec.".format(self.CHECK_CONNECTION_TIMEOUT))
            return -1