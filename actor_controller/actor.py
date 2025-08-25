import os, re
from typing import Any, List, Optional, Union

from ic.canister import Canister
from ic.candid import encode, decode
try:
    from ic.principal import Principal as ICPrincipal  # for isinstance checks
except Exception:
    ICPrincipal = None  # library might not expose at import time

from utils.parsers.subacount_parsers import transform_login_result
from .agent import ICAgent

DECODE_ERRORS = (
    "Cannot find field",
    "Message length smaller",
    "IDL error",
)

# ---------- DID parsing helpers (dynamic; no hardcoded mappings) ----------

def _strip_candid_comments(src: str) -> str:
    """Remove // line and /* block */ comments."""
    src = re.sub(r"//.*?$", "", src, flags=re.M)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return src

def _iter_balanced_blocks(src: str, keyword: str):
    """
    Yield inner text for '<keyword> { ... }' blocks with nested braces handled.
    Works for 'record' and 'variant'.
    """
    i, n = 0, len(src)
    kw = keyword
    while i < n:
        j = src.find(kw, i)
        if j < 0:
            break
        k = j + len(kw)
        while k < n and src[k].isspace():
            k += 1
        if k >= n or src[k] != "{":
            i = j + 1
            continue
        depth, start = 0, k + 1
        k += 1
        while k < n:
            c = src[k]
            if c == "{":
                depth += 1
            elif c == "}":
                if depth == 0:
                    yield src[start:k]
                    i = k + 1
                    break
                depth -= 1
            k += 1
        else:
            break

class ICActor:
    def __init__(self, agent: ICAgent, canister_id: str):
        self.agent = agent
        self.canister_id = canister_id

        candid_interface = self._load_candid_interface()
        if not candid_interface:
            raise RuntimeError("Could not load Candid interface from .did file")

        self._candid_text = candid_interface
        self._hash_to_name = self._build_field_hash_map(candid_interface)

        self.canister = Canister(
            agent=agent.agent,
            canister_id=canister_id,
            candid=candid_interface,
        )

    # --------- hashing / DID map ---------

    def _candid_hash(self, name: str) -> int:
        """Candid field-id hash: foldl(h*223 + byte) mod 2^32."""
        h = 0
        for b in name.encode("utf-8"):
            h = (h * 223 + b) & 0xFFFFFFFF
        return h

    def _load_candid_interface(self) -> str:
        try:
            did_file_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "canisters", "m_autonome_canister.did"
            )
            with open(did_file_path, "r") as f:
                candid_text = f.read()
            print(f"Loaded Candid interface from {did_file_path} ({len(candid_text)} chars)")
            return candid_text
        except Exception as e:
            print(f"Failed to load Candid interface: {e}")
            return ""

    def _build_field_hash_map(self, did_text: str) -> dict[int, str]:
        """
        Parse the .did and collect ALL record field names and variant alt names
        (including unit alts like 'oneOnOne;'), then map candid-hash -> name.
        """
        src = _strip_candid_comments(did_text)
        names: set[str] = set()

        # record { "field" : T; field : T; ... }
        for body in _iter_balanced_blocks(src, "record"):
            for m in re.finditer(r'(?:"([^"]+)"|([A-Za-z_][\w-]*))\s*:', body):
                nm = m.group(1) or m.group(2)
                if nm:
                    names.add(nm)

        # variant { Alt; "Alt"; Alt : T; "Alt" : T; ... }
        reserved = {
            "null","bool","text","blob","nat","nat8","nat16","nat32","nat64",
            "int","int8","int16","int32","int64","float32","float64","principal",
            "vec","opt","record","variant","service","func","oneway",
        }
        ident = r'[A-Za-z_][\w-]*'
        for body in _iter_balanced_blocks(src, "variant"):
            # Quoted alts (allow followed by :, }, , or ;)
            for m in re.finditer(r'"([^"]+)"\s*(?=[:},;])', body):
                nm = m.group(1).strip()
                if nm:
                    names.add(nm)
            # Bare alts (unit or typed) — allow :, }, , or ;
            for m in re.finditer(rf'({ident})\s*(?=[:}},;])', body):
                nm = m.group(1)
                if nm and nm not in reserved:
                    names.add(nm)

        # common arms
        names.update({"ok", "err"})

        mapping = {self._candid_hash(n): n for n in names}
        print(f"Built hash->name map with {len(mapping)} entries")
        return mapping

    # --------- tree normalization (dynamic) ---------

    def _rehydrate_hashed_keys(self, obj: Any) -> Any:
        """
        Rename keys like '_3535639105' back to their Candid names using the map
        we built from the .did, recursively.
        """
        if isinstance(obj, dict):
            newd = {}
            for k, v in obj.items():
                newk = k
                if isinstance(k, str) and k.startswith("_") and k[1:].isdigit():
                    try:
                        h = int(k[1:])
                        mapped = self._hash_to_name.get(h)
                        if mapped:
                            newk = mapped
                    except ValueError:
                        pass
                newd[newk] = self._rehydrate_hashed_keys(v)
            return newd
        if isinstance(obj, list):
            return [self._rehydrate_hashed_keys(x) for x in obj]
        return obj

    def _unwrap_unit_variants_inplace(self, obj: Any) -> None:
        """
        Convert objects like {'oneOnOne': None} into 'oneOnOne' (unit variants),
        across the whole structure.
        """
        if isinstance(obj, dict):
            if len(obj) == 1:
                (k, v), = obj.items()
                if v is None:
                    obj.clear()
                    obj["__unit__"] = k  # temporary marker replaced in parent
                    return
            for key in list(obj.keys()):
                val = obj[key]
                self._unwrap_unit_variants_inplace(val)
                if isinstance(val, dict) and "__unit__" in val and len(val) == 1:
                    obj[key] = val["__unit__"]
        elif isinstance(obj, list):
            for i in range(len(obj)):
                self._unwrap_unit_variants_inplace(obj[i])

    def _convert_principals_inplace(self, obj: Any) -> Any:
        """
        Replace any ic.principal.Principal instances with their text form
        (e.g., 'aaaaa-aa...') so the result is JSON-serializable.
        """
        if ICPrincipal is None:
            return obj
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                obj[k] = self._convert_principals_inplace(v)
            return obj
        if isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = self._convert_principals_inplace(v)
            return obj
        if isinstance(obj, ICPrincipal):
            return obj.to_str() if hasattr(obj, "to_str") else str(obj)
        return obj

    # --------- calling ---------

    async def call_method(
        self,
        method_name: str,
        args: Optional[List[Any]] = None,
        *,
        return_type: Optional[str] = None,
        enable_fallback: bool = True,
    ):
        # try:
        #     print(f"Calling canister method (wrapper): {method_name}")
        #     method = getattr(self.canister, method_name)
        #     result = method(*args) if args else method()

        #     # dynamic cleanup on wrapper path
        #     result = self._rehydrate_hashed_keys(result)
        #     self._unwrap_unit_variants_inplace(result)
        #     result = transform_login_result(result)      # subaccounts to HEX
        #     result = self._convert_principals_inplace(result)  # principals to text
        #     print("Wrapper result:", type(result))
        #     return result

        # except Exception as e:
        #     msg = str(e)
        #     print(f"Wrapper raised: {msg}")

        #     if not enable_fallback or not any(s in msg for s in DECODE_ERRORS):
        #         return {"status": "error", "message": msg}

            try:
                raw_or_tree = self._raw_call(method_name, args)

                # A) If we got true Candid bytes -> decode using return type (auto or provided)
                if isinstance(raw_or_tree, (bytes, bytearray)):
                    rtype = return_type or self._extract_return_type(method_name)
                    print(f"Return type: {rtype}")
                    if rtype:
                        decoded = decode(raw_or_tree, rtype)
                    else:
                        # last resort: try a permissive variant probe
                        try:
                            which = decode(raw_or_tree, "variant { err : reserved; ok : reserved }")
                            decoded = which  # at least return which arm
                        except Exception:
                            return {"status": "raw-bytes", "bytes": raw_or_tree}

                    decoded = self._rehydrate_hashed_keys(decoded)
                    self._unwrap_unit_variants_inplace(decoded)
                    decoded = transform_login_result(decoded)
                    decoded = self._convert_principals_inplace(decoded)
                    return decoded

                # B) ic-py returned a Python structure (ids as keys) -> hydrate & normalize
                print("Raw call returned a Python structure; rehydrating hashed field names...")
                hydrated = self._rehydrate_hashed_keys(raw_or_tree)
                self._unwrap_unit_variants_inplace(hydrated)
                hydrated = transform_login_result(hydrated)
                hydrated = self._convert_principals_inplace(hydrated)
                return hydrated

            except Exception as e2:
                return {"status": "error", "message": f"fallback decode failed: {e2}"}

    def _is_query(self, method_name: str) -> bool:
        mname = re.escape(method_name)
        pattern = rf'(?:"{mname}"|\b{mname}\b)\s*:\s*\([^)]*\)\s*->\s*\([^)]*\)\s*query\b'
        return re.search(pattern, self._candid_text, flags=re.IGNORECASE) is not None

    def _extract_return_type(self, method_name: str) -> Optional[str]:
        """
        Pull the declared return type for a method from the textual .did.
        Returns the raw type expression inside the (...) after '->'.
        """
        mname = re.escape(method_name)
        pat = rf'(?:"{mname}"|\b{mname}\b)\s*:\s*\([^)]*\)\s*->\s*\(([^)]*)\)'
        m = re.search(pat, self._candid_text, flags=re.IGNORECASE | re.S)
        ret = m.group(1).strip() if m else None
        if ret:
            snippet = ret[:120]
            print(f"extracted return type for {method_name}: {snippet}{'...' if len(ret) > 120 else ''}")
        else:
            print(f"could not extract return type for {method_name}")
        return ret

    def _raw_call(self, method_name: str, args: Optional[List[Any]]) -> Union[bytes, dict, list]:
        """
        Submit a raw call and return either:
          - Candid reply bytes (preferred), or
          - a Python structure already decoded by ic-py (list/dict with hashed keys).
        """
        print(f"Raw call: {method_name} with args: {args}")
        arg_blob = encode(args or [])  # () -> encode([])
        can_id = getattr(self.canister, "canister_id", None) or getattr(self.canister, "_canister_id")
        if not can_id:
            raise RuntimeError("Cannot find canister id on Canister instance")

        if self._is_query(method_name):
            print("raw query_raw() fallback")
            raw = self.agent.agent.query_raw(can_id, method_name, arg_blob)
        else:
            print("raw update_raw() fallback")
            raw = self.agent.agent.update_raw(can_id, method_name, arg_blob)

        if isinstance(raw, tuple) and isinstance(raw[0], (bytes, bytearray)):
            return raw[0]
        return raw

    # --- Introspection helper (unchanged) ---
    def get_methods(self):
        return self._exposed_methods()

    def _exposed_methods(self):
        names = []
        for name in dir(self.canister):
            if name.startswith("_"):
                continue
            attr = getattr(self.canister, name)
            if callable(attr):
                names.append(name)
        return sorted({n[:-6] if n.endswith("_async") else n for n in names})
