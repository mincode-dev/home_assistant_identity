# subaccount_utils.py
from __future__ import annotations
from typing import Any
import copy

# --- core converters ---------------------------------------------------------

def _parse_opt_blob_to_hex(opt_blob: Any) -> str:
    """
    Convert an 'opt blob' encoded as [] or [[int,...]] into an uppercase HEX string.
    - []              -> ""  (none)
    - [[96, 252, ...]] -> "60FC..." (uppercase)
    """
    if not opt_blob:
        return ""
    # Expected shape: a 1-length list containing the list of byte ints.
    if isinstance(opt_blob, list) and len(opt_blob) == 1 and isinstance(opt_blob[0], list):
        blob = opt_blob[0]
        try:
            return bytes(blob).hex().upper()
        except Exception:
            # Fallback: do it nibble-by-nibble (faithful port of your JS)
            return parse_subaccount_to_text_py(blob)
    # If for some reason the blob already arrives as raw list-of-bytes:
    if isinstance(opt_blob, list) and all(isinstance(x, int) for x in opt_blob):
        return bytes(opt_blob).hex().upper()
    # Unknown shape — leave as-is (or return "")
    return ""

def parse_subaccount_to_text_py(value: list[int]) -> str:
    """
    Pythonic equivalent of your JS function:
      value: [int, ...] (0..255) -> "AABBCC..." (uppercase hex)
    """
    return bytes(value).hex().upper()

# --- tree transformer --------------------------------------------------------

_SUBACCOUNT_KEYS = ("icpDefaultSubaccount", "businessDefaultSubaccount")

def convert_subaccounts_inplace(obj: Any) -> None:
    """
    Walk a nested structure (dict/list) and convert any
    'icpDefaultSubaccount' / 'businessDefaultSubaccount' fields from
    [] or [[int,...]] to uppercase HEX strings. Mutates in place.
    """
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in _SUBACCOUNT_KEYS:
                obj[k] = _parse_opt_blob_to_hex(v)
            else:
                convert_subaccounts_inplace(v)
    elif isinstance(obj, list):
        for i in range(len(obj)):
            convert_subaccounts_inplace(obj[i])

def transform_login_result(data: Any, *, inplace: bool = False) -> Any:
    """
    Convert subaccount fields across the entire payload.
    If inplace=False (default), returns a deep-copied transformed object.
    """
    target = data if inplace else copy.deepcopy(data)
    convert_subaccounts_inplace(target)
    return target

# --- demo / example ----------------------------------------------------------

# if __name__ == "__main__":
#     # Minimal example showing how to use with your payload shape.
#     import json, sys

#     # If you pipe your JSON into this script, it will transform and print it.
#     #   cat payload.json | python subaccount_utils.py
#     try:
#         raw = json.load(sys.stdin)
#     except Exception:
#         print("No JSON on stdin; running a tiny self-test.")
#         raw = {
#             "status": "success",
#             "result": [{
#                 "type": "rec_129",
#                 "value": {
#                     "ok": {
#                         "contacts": [{
#                             "id": 1,
#                             "icpDefaultSubaccount": [[96, 252, 6, 143]],  # -> "60FC068F"
#                             "businessDefaultSubaccount": []
#                         }]
#                     }
#                 }
#             }]
#         }

#     transformed = transform_login_result(raw, inplace=False)
#     print(json.dumps(transformed, indent=2))
