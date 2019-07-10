import logging
import async_timeout
from sysutils.utils.timer import Timer
from cassandra.util import OrderedMapSerializedKey, SortedSet
from sysutils.debug import nice_print
from .query_helper import inject_column_name
from .system_adapter import CassandraSystemDataAdapter

_logger = logging.getLogger(__name__)


class CassandraDataAdapter(CassandraSystemDataAdapter):
    DEFAULT_SELECT_LIMIT = 1000

    def __init__(self, loop, connection_string=None, port=None, nodes=None, **kwargs):
        super().__init__(loop, connection_string=connection_string, port=port, nodes=nodes)
        self.read_only = kwargs.get("read_only") or False

    def field_all_names_for_select(self, table_name: str, keyspace_name: str):
        pass

    async def fetch(self,
                     table_name: str,
                     schema: (str, None) = None,
                     fields: list = None,
                     limit: int = -1,
                     offset: int = 0,
                     condition: str = None,
                     **kwargs
                     ) -> (dict, dict):

        limit = self.DEFAULT_SELECT_LIMIT if limit == -1 else limit
        with Timer() as timer:

            model, fields = await self.get_column_info(table_name, schema)

            fields_str = ", ".join(fields)
            cql = "SELECT {} from {}.{} limit {}".format(fields_str, schema, table_name, limit)
            _logger.info("CQL: [" + cql + "]")

            rows = await self.execute_select(cql)
            data = await inject_column_name(rows, fields)
        meta = {
            "time": timer.elapsed,
            "sql": cql,
            "model": model,
        }
        return data, meta


    @staticmethod
    def compose_empty_row(tab_fields):
        return {x: "" for x in tab_fields}

    @staticmethod
    def prep_statement_insert_update(table_name,
                                     column_names,
                                     primary_key,
                                     values):
        columns_string = ", ".join(column_names)
        primary_key = ", ".join(primary_key) if isinstance(primary_key, list) else primary_key
        b = ['%s']*len(column_names)
        a = ", ".join(b)
        prepared_statement = f"""INSERT INTO {table_name} ({columns_string})
        VALUES ({a}) """
        # prepared_statement = f"""INSERT INTO {table_name} ({columns_string})
        # VALUES (1, {values[1]}) """
        return prepared_statement

    # TODO do it after schema
    async def execute_insert_update(self,
                                    table_name: str,
                                    column_names: list,
                                    values: list,
                                    schema: list or None = None,
                                    primary_key=None,
                                    *args, **kwargs):
        if self.read_only:
            _logger.info("Read Only Connection. CAnnot insert or update")
            return None
        if schema:
            table_name = schema + "." + table_name
        # values_string = ''
        # for each in values:
        #     values_string += " '"+str(each)+"'"+", "

        # values_string = ", ".join(values)
        cql = self.prep_statement_insert_update(table_name,
                                                column_names,
                                                primary_key,
                                                values
                                                )
        try:
            conn = await self.create_conn()
            # prepared = conn.get_prepared(cql)
            # print(f"prepared CQL ======== {prepared}")
            return await conn.execute_wait_result(cql, values)
        except Exception as error:
            _logger.warning("Cannot execute SQL '{}'; Exception: {}".format(cql[0:30], error))
            return None
