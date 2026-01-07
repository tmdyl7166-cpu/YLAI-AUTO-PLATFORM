import itertools
import random
import string
from typing import Iterable, Dict, Any, List

SPECIALS = ['"', "'", '<', '>', '&', '\\', '/', '\n', '\r', '\t', '%', '#', '?']
BOUNDARIES_INT = [-1, 0, 1, 2**31-1, -2**31]
BOUNDARIES_LEN = [0, 1, 10, 100, 1000]

def mutate_strings(seed: str) -> Iterable[str]:
    yield seed
    yield seed.upper()
    yield seed.lower()
    yield ''.join(reversed(seed))
    for ch in SPECIALS:
        yield seed + ch
        yield ch + seed
    for l in BOUNDARIES_LEN:
        yield seed + 'A'*l

def mutate_numbers(seed: int) -> Iterable[int]:
    for v in itertools.chain([seed], BOUNDARIES_INT, [seed*2, seed-1]):
        yield v

def mutate_json(seed: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    yield seed
    # remove keys
    if seed:
        k = next(iter(seed.keys()))
        m = dict(seed)
        m.pop(k, None)
        yield m
    # wrong types
    for key in seed.keys():
        m = dict(seed)
        m[key] = '"'  # force wrong type
        yield m

def generate_cases(endpoint: str, method: str, base_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    cases = []
    for k, v in base_params.items():
        if isinstance(v, str):
            variants = list(mutate_strings(v))
        elif isinstance(v, (int, float)):
            variants = list(mutate_numbers(int(v)))
        elif isinstance(v, dict):
            variants = list(mutate_json(v))
        else:
            variants = [v]
        for alt in variants:
            case = dict(base_params)
            case[k] = alt
            cases.append(case)
    return cases
