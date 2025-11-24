from output.client import Client
from output.model import UserWhere, UserOption
import output.model
import output.selector as selector
from output.operations import *
from output.selector import UserSelector
import dacite


client = Client(endpoint="http://127.0.0.1:8001/api/v1/graphql")
client.headers = {
    'authorization': ''
}

client.session.verify = False


res = QueryUsers().where(
        UserWhere(name_REGEX="tom")
    ).option(
        UserOption(limit=10)
    ).select(
        UserSelector().
            select('id', 'name', 'createdAt').
        userGroups(UserGroupSelector().
            select('id', 'name'))
    ).do(client)

# print(res[0].id)
for u in res:
    print(u.id)
    print(u.name)
    print(u.userGroups)

user_count = CountUsers().where(
        UserWhere(
            # name_REGEX="tom"
        )
     ).do(client)

print('user count:', user_count)