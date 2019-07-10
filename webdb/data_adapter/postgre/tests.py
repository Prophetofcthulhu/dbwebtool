from webdb.data_adapter.postgre.base_adaptor import PostgreSQLAdaptor
import asyncio
from webdb.sysutils.asynchronous.utils import get_from_queue


async def test():
    dsn = 'dbname=test_db user=**** password=**** host=192.168.0.105 port=54832'
    # bd_path = "./my_sqlite.sqlite3"
    table_name = "xxx_test_db"
    names_types = [
        {"name": "ID", "type": "int", "PK": True},
        {"name": "date", "type": "text", },
    ]
    select = "SELECT * FROM xxx_test_db"
    insert = "INSERT INTO xxx_test_db values (1, 'hello'), (2, 'goodbey' )"
    drop = "DROP TABLE xxx_test_db"
    status = []
    adaptor = PostgreSQLAdaptor(loop=loop, dsn=dsn)
    await adaptor.create_table_model(table_name, names_types)
    status.append(adaptor.status_last_transaction)
    await adaptor.execute_sql(insert)
    status.append(adaptor.status_last_transaction)
    result = await adaptor.execute_sql(sql=select)
    status.append(adaptor.status_last_transaction)
    await adaptor.execute_sql(sql=drop)
    status.append(adaptor.status_last_transaction)
    return result, status


async def test_system():
    dsn = 'dbname=test_db user=**** password=**** host=192.168.0.105 port=54832'
    # bd_path = "./my_sqlite.sqlite3"
    table_name = "humans"
    select = "SELECT COLUMN_NAME data_type, udt_name FROM information_schema.COLUMNS WHERE TABLE_NAME = '{}';".format(table_name)
    status = []
    adaptor = PostgreSQLAdaptor(loop=loop, dsn=dsn)
    result = await adaptor.execute_sql(sql=select)
    status.append(adaptor.status_last_transaction)
    return result, status

async def test_consumer():
    dsn = 'dbname=test_db user=**** password=**** host=192.168.0.105 port=54832'
    # bd_path = "./my_sqlite.sqlite3"
    table_name = "xxx_test_db"
    names_types = [
        {"name": "ID", "type": "int", "PK": True},
        {"name": "date", "type": "text", },
    ]
    select = "SELECT * FROM xxx_test_db"
    insert = "INSERT INTO xxx_test_db values (1, 'hello'), (2, 'goodbey' )"
    drop = "DROP TABLE xxx_test_db"
    status = []
    adaptor = PostgreSQLAdaptor(loop=loop, dsn=dsn)
    await adaptor.create_table_model(table_name, names_types)
    status.append(adaptor.status_last_transaction)
    await adaptor.execute_sql(insert)
    system = await adaptor.get_column_info(table_name)
    print(system) if system else status.append("EVERYTHING GONE TERRIBLY WRONG")
    status.append(adaptor.status_last_transaction)
    await adaptor.consume(sql=select)
    result = []
    result = await get_from_queue(adaptor._queue)
    status.append(adaptor.status_last_transaction)
    await adaptor.execute_sql(sql=drop)
    status.append(adaptor.status_last_transaction)
    return result, status

# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     asyncio.set_event_loop(loop)
#     future = asyncio.ensure_future(test())
#     loop.run_until_complete(future)
#     print("_____I'M RESULT:{}!!!!!!".format(future.result()[0]))
#     print("{}".format("-------" + "-------\n--------".join(future.result()[1])+"--------"))
#

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.ensure_future(test_system())
    loop.run_until_complete(future)
    print("_____I'M RESULT:{}!!!!!!".format(future.result()[0]))
    print("{}".format("-------" + "-------\n--------".join(future.result()[1])+"--------"))

