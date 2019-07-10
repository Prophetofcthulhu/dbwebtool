from sysutils.asynchronous.broker.redis.redis_broker import RedisBroker
import asyncio
import aioredis


class Redis(RedisBroker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result_data = None

    # #TODO with async with self.pool.get() as conn:
    # async def get_connection(self):
    #     await self.connect()
    #     return aioredis.Redis(await self.pool.get())
    #
    # @property
    # async def connection(self):
    #     from aioredis.pool import _AsyncConnectionContextManager
    #     await self.connect()
    #     conn = self.pool.get()
    #     conn.open()
    #     print(conn)
    #     return aioredis.Redis(conn)

    async def get_velue(self, key, field):
        await self.connect()
        async with self.pool.get() as conn:
            conn = aioredis.Redis(conn)
            self.result_data = await conn.hget(key, field)

    # async def get_velue(self, key, field):
    #     conn = await self.connection
    #     self.result_data = await conn.hget(key, field)

    async def get_keys_pattern(self, params):
        await self.connect()
        async with self.pool.get() as conn:
            conn = aioredis.Redis(conn)
            self.result_data = await conn.keys(params["pattern"])
