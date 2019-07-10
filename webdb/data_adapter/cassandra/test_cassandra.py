import webdb.data_adapter.sqlite.base_adaptor as adaptors
import pytest
import asyncio
import io
from sysutils.asynchronous.utils import get_from_queue
from webdb.data_adapter.cassandra.adapter import CassandraDataAdapter

@pytest.mark.asyncio
async def test_create_insert_update_delete(event_loop):
    bd_path = "nodes=[193.24.30.63] port=9042"
    table_name = "mock.images"
    names_types = [
        {"name": "ID", "type": "int", "PK": True},
        {"name": "image", "type": "blob", },
    ]
    column_names = ["id", "image"]
    sql_select = "SELECT * FROM images"
    sql_insert = "INSERT INTO mock.images values ({},{})"
    # sql_drop_table = "DROP TABLE test"
    with open("../../../images/download.jpeg", "rb") as f:
        image = f.read()
    print(bytearray(image))
    # image = bytearray(image)
    # image = io.BytesIO(image)
    # print(image)
    values = [1, image]
    adaptor = CassandraDataAdapter(loop=event_loop, connection_string=bd_path)
    await adaptor.broker.connect()
    #todo byte stream
    await adaptor.create_table_model(table_name, names_types)
    await adaptor.execute_insert_update(table_name=table_name,
                                        column_names=column_names,
                                        values=values)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(test_create_insert_update_delete(loop))
    loop.run_until_complete(future)
