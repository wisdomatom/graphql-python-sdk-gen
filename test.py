from output.client import Client
from output.model import CategoryOption, CategoryWhere, ProductOption, ProductWhere, UserGroupOption, UserGroupWhere, UserWhere, UserOption, UserHas
from output.operations import QueryUsers, CountUsers, QueryCategorys
from output.selector import CategorySelector, ProductSelector, UserSelector, UserGroupSelector
import os
from output.field import FieldCategory, FieldUser, FieldUserGroup, FieldProduct


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
        userGroups(
            UserGroupWhere(),
            UserGroupOption(),
            UserGroupSelector().
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

res = QueryCategorys().where(
        CategoryWhere()
    ).option(
        CategoryOption()
    ).select(
        CategorySelector().select(
            FieldCategory.id,
            FieldCategory.name
        ).children(
            CategoryWhere(),
            CategoryOption(),
            CategorySelector().select(
                FieldCategory.id,
                FieldCategory.name
            ).children(
                CategoryWhere(name='aha'),
                CategoryOption(),
                CategorySelector().select(
                    FieldCategory.id,
                    FieldCategory.name
                )
            ).parent(
                CategoryWhere(),
                CategoryOption(),
                CategorySelector().select(
                    FieldCategory.id,
                    FieldCategory.name
                )
            ).products(
                ProductWhere(),
                ProductOption(),
                ProductSelector().select(
                    FieldProduct.id,
                    FieldProduct.name
                )
            )
        )
    ).do(client)
print('category:', res)