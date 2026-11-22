# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Bytecode test that Serve.run is the only Serve method that loads check_retro
# relates: [clutch/serve.py]
# owner: clutch/serve.py
# verified: 2182d51e
# hash: 7f05f880e0c07ea7c48c8f03501f21ae633ba432c832e3689ff3bfbda2c08812
import dis
import inspect
from types import CodeType

from clutch.serve import Serve


def loads(code):
    found = [instruction for instruction in dis.get_instructions(code) if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"} and instruction.argval == "check_retro"]
    for constant in code.co_consts:
        if isinstance(constant, CodeType):
            found.extend(loads(constant))
    return found


def test_only_run_loads_check_retro():
    sites = {name: loads(member.__code__) for name, member in inspect.getmembers(Serve, inspect.isfunction)}
    assert len(sites["run"]) == 1
    assert not sites["merge"]
    assert not sites["__init__"]
    assert sum(map(len, sites.values())) == 1
