from output.client import Client
from output.model import UserWhere, UserOption
import output.model
import output.selector as selector
from output.operations import Queryusers

client = Client(endpoint="http://127.0.0.1:8001/api/v1/graphql")
client.headers = {
    'authorization': ''
}

res = Queryusers().where(
        UserWhere(name="tom")
    ).option(
        UserOption(limit=10)
    ).select(
       lambda q: (
        q.select("id", "name", "createdAt").addresses().select("id","name")
       )
    ).do(client)

print(res)