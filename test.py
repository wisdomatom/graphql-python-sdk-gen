from output.client import Client
from output.model import UserWhere, UserOption
from output.operations import *
from output.selector import UserSelector
import os
from output.field import *


client = Client(endpoint="http://127.0.0.1:8001/api/v1/graphql")
client.headers = {
    'authorization': os.environ['token']
}

client.session.verify = False


res = QueryUsers().where(
        UserWhere(name_REGEX="tom",HAS=[UserHas.name])
    ).option(
        UserOption(limit=10)
    ).select(
        UserSelector().
            select(FieldUser.id, FieldUser.name, FieldUser.createdAt).
        userGroups(UserGroupSelector().
            select(FieldUserGroup.id, FieldUserGroup.name))
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