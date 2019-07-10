import webdb.data_adapter.sqlite.base_adaptor as adaptors
import pytest
from sysutils.asynchronous.utils import get_from_queue


@pytest.mark.asyncio
async def test_create_insert_update_delete(event_loop):
    bd_path = "./my_sqlite.sqlite3"
    table_name = "test"
    names_types = [
        {"name": "ID", "type": "int", "PK": True},
        {"name": "date", "type": "text", },
    ]
    sql_select = "SELECT * FROM test"
    sql_insert = "INSERT INTO test values (1, 'hello'), (2, 'goodbey' )"
    sql_drop_table = "DROP TABLE test"

    adaptor = adaptors.SqliteBaseAdaptor(loop=event_loop, database_file_path=bd_path)
    await adaptor.create_table_model(table_name, names_types)
    await adaptor.execute_insert_update(sql=sql_insert)
    future2 = await adaptor.execute_select(sql=sql_select)
    assert future2 == [(1, 'hello'), (2, 'goodbey')]
    await adaptor.execute_insert_update(sql_drop_table)


@pytest.mark.asyncio
async def test_consume(event_loop):
    bd_path = "./my_sqlite.sqlite3"
    select = "SELECT * FROM Hello"

    adaptor = adaptors.SqliteBaseAdaptor(loop=event_loop, database_file_path=bd_path)
    await adaptor.start_consume(sql=select)
    result = []
    await get_from_queue(adaptor._queue, result=result)
    assert result == [(1, 'hello'), (2, 'goodbey')]
    print(result)



