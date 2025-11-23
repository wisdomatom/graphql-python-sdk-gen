from output.client import Client
from output.model import UserWhere, UserOption
import output.model
import output.selector as selector
from output.operations import Queryusers
from output.selector import UserSelector


client = Client(endpoint="http://127.0.0.1:8001/api/v1/graphql")
client.headers = {
    'authorization': 'asdcIEHlshs.>w*3#X<'
}

client.session.verify = False


res = Queryusers().where(
        UserWhere(name="wisdomatom")
    ).option(
        UserOption(limit=10)
    ).select(
       lambda q: (
        q.select("id", "name", "createdAt").userGroups(
            lambda q: (
                q.select("id")
            )
        )
       )
    ).do(client)

print(res)