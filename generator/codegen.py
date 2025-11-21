# generator/codegen.py
import json
import os
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# Simple data classes (not using dataclass here to keep dependency minimal in generator)
def load_introspection(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_type_maps(introspection: Dict[str, Any]):
    types = introspection.get("data", {}).get("__schema", {}).get("types", [])
    type_map = {t["name"]: t for t in types if "name" in t}
    object_names = [t["name"] for t in types if t.get("kind") == "OBJECT" and not t["name"].startswith("__")]
    return types, type_map, object_names

# Utilities to extract GraphQL inner type name and whether list/non-null
def extract_graphql_type(t: Dict[str, Any]):
    """
    Return (name, is_list, is_non_null)
    """
    kind = t.get("kind")
    if kind == "NON_NULL":
        return extract_graphql_type(t["ofType"])
    if kind == "LIST":
        name, _, _ = extract_graphql_type(t["ofType"])
        return name, True, False
    # base case
    return t.get("name"), False, False

def gql_type_to_python(t: Dict[str, Any], scalar_map: Dict[str, str]) -> str:
    """
    Map GraphQL type to python typing string (primitive mapping via scalar_map).
    Keep it simple: list -> List[...], optional -> Optional[...]
    """
    # walk down for NON_NULL / LIST
    def walk(node):
        if node is None:
            return ("Any", False)
        k = node.get("kind")
        if k == "NON_NULL":
            inner, is_list = walk(node.get("ofType"))
            return (inner, is_list)
        if k == "LIST":
            inner, _ = walk(node.get("ofType"))
            return (f"List[{inner}]", True)
        # scalar or object
        name = node.get("name")
        if name in scalar_map:
            return (scalar_map[name], False)
        # object/input/enum -> use name as is
        return (name, False)
    res, _ = walk(t)
    return res

def unwrap_type(t):
    # remove list brackets and non-null
    return t.replace("[", "").replace("]", "").replace("!", "")

def prepare_template_context(types: List[Dict[str, Any]], type_map: Dict[str, Any], object_names: List[str]):
    # Default scalar map (you can extend)
    scalar_map = {
        "String": "str",
        "ID": "str",
        "Int": "int",
        "Float": "float",
        "Boolean": "bool",
        "DateTime": "datetime.datetime",
        "UUID": "str",
        "ScalarDateTime": "datetime.datetime",
        "ScalarInt": "int",
        "ScalarJson": "dict"
    }

    # Build a list of simple type descriptors for templates
    models = []
    enums = []
    inputs = []
    interfaces = []

    object_type_names = set(x["name"] for x in types if x.get("kind") == "OBJECT" or x.get("kind") == "INTERFACE")

    for t in types:
        name = t.get("name")
        if not name or name.startswith("__"):
            continue
        kind = t.get("kind")
        if kind == "ENUM":
            enums.append({"name": name, "values": [ev["name"] for ev in t.get("enumValues", [])]})
            continue
        if kind == "INPUT_OBJECT":
            fields = []
            for f in t.get("inputFields", []):
                pytype = gql_type_to_python(f["type"], scalar_map)
                fields.append({"name": f["name"], "type": pytype})
            inputs.append({"name": name, "fields": fields})
            continue
        if kind == "OBJECT":
            # skip Query and Mutation roots (they will be used for operations)
            if name in ("Query", "Mutation"):
                continue
            fields = []
            for f in t.get("fields", []):
                pytype = gql_type_to_python(f["type"], scalar_map)
                fields.append({
                    "name": f["name"], 
                    "type": pytype,
                    "raw_type": unwrap_type(pytype),
                    "is_object": unwrap_type(f["name"]) in object_type_names
                    })
            models.append({"name": name, "fields": fields, "interfaces": [i["name"] for i in t.get("interfaces", [])]})
            continue
        if kind == "INTERFACE":
            fields = []
            for f in t.get("fields", []):
                pytype = gql_type_to_python(f["type"], scalar_map)
                fields.append({"name": f["name"], "type": pytype})
            interfaces.append({"name": name, "fields": fields})
            continue

    # extract operations (Query/Mutation root fields)
    query_root = type_map.get("Query", {})
    mutation_root = type_map.get("Mutation", {})
    ops = []
    for root, kind in [(query_root, "query"), (mutation_root, "mutation")]:
        if not root:
            continue
        for f in root.get("fields", []):
            # args
            args = []
            for a in f.get("args", []):
                args.append({"name": a["name"], "type": gql_type_to_python(a["type"], scalar_map)})
            # return type name and is_list
            ret_name, is_list, _ = extract_graphql_type(f["type"])
            ops.append({
                "name": f["name"],
                "kind": kind,
                "args": args,
                "return_type": ret_name,
                "return_is_list": is_list,
            })

    ctx = {
        "models": models,
        "inputs": inputs,
        "enums": enums,
        "interfaces": interfaces,
        "ops": ops,
        "scalar_map": scalar_map,
        "object_names": object_names,
    }
    return ctx

def render_all(introspection_path: str, out_dir: str = None):
    if out_dir is None:
        out_dir = OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    intros = load_introspection(introspection_path)
    types, type_map, object_names = build_type_maps(intros)
    ctx = prepare_template_context(types, type_map, object_names)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    templates = ["model.j2", "selector.j2", "client.j2", "operations.j2"]
    for tpl in templates:
        template = env.get_template(tpl)
        out = template.render(ctx)
        out_path = os.path.join(out_dir, tpl.replace(".j2", ".py"))
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out)
        print("Wrote", out_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GraphQL -> Python dataclass SDK generator (templates)")
    parser.add_argument("introspection", help="Path to introspection JSON file")
    parser.add_argument("--out", help="Output directory", default=None)
    args = parser.parse_args()
    render_all(args.introspection, args.out)
