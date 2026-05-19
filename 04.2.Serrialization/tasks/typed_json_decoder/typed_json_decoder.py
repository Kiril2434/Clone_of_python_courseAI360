import typing as tp
import json

from decimal import Decimal


def decode_typed_json(json_value: str) -> tp.Any:
    """
    Returns deserialized object from json string.
    Checks __custom_key_type__ in object's keys to choose appropriate type.

    :param json_value: serialized object in json format
    :return: deserialized object
    """
    def object_hook(obj: dict[str, tp.Any]) -> dict[tp.Any, tp.Any]:
        key_type = obj.pop("__custom_key_type__", None)
        if key_type is None:
            return obj
        type_map: dict[str, tp.Callable[[str], tp.Any]] = {
            "int": int,
            "float": float,
            "decimal": Decimal,
        }
        convert = type_map[key_type]
        return {convert(k): v for k, v in obj.items()}

    return json.loads(json_value, object_hook=object_hook)
