# from https://groups.google.com/a/lists.datastax.com/forum/#!topic/python-driver-user/WMPg2WXis7M

import json
import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table


class Person(Model):
    __table_name__ = 'useridindex'
    __keyspace__ = 'testdb'
    __connection__ = 'cluster2'

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    first_name = columns.Text()
    last_name = columns.Text()
    assets_idx = columns.Set(columns.Integer())

    def get_data(self):
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            # 'assets_idx': self.........
        }


# def cassandraTest():
#     cluster = Cluster(contact_points=['localhost'], port=9042)
#     session = cluster.connect()
#
#     connection.register_connection('cluster2', session=session)
#     create_keyspace_simple('testdb', 1, connections=['cluster2'])
#     sync_table(Person)
#
#     Person.create(first_name='jack', last_name='chen', assets_idx={111, 2222, 3333})
#     Person.save()
#     persons = Person.objects().all()
#
#     jsonObj = [person.get_data() for person in persons]
#
#     print(json.dumps(jsonObj, indent=4, ensure_ascii=False));
#
#
# if __name__ == '__main__':
#     cassandraTest()
