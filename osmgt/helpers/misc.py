from typing import Dict
from typing import List
from typing import Union
from typing import Any


def find_list_dicts_from_key_and_value(
    input_dict: List[Dict], key: str, value: Union[Any]
) -> int:

    for list_idx, values in enumerate(input_dict):
        if values.get(key, None) == value:
            return list_idx
    else:
        raise ValueError(f"{key} == {value} not found")
