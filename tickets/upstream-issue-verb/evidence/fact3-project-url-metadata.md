# Fact 3: `Project-URL` from installed clutchwork metadata

Captured 2026-11-16 UTC at HEAD `31327358`. Commits landed during the run up to `a7b7329a` were ticket files only and did not touch `pyproject.toml`, `clutch/observe.py`, `README.md` or `clutch/docs/host-contract.md`. The distribution is `clutchwork`, and the import package is `clutch` (`pyproject.toml`: `name = "clutchwork"`, `[tool.uv.build-backend] module-name = "clutch"`, `[project.urls] Repository = "https://github.com/protus75/clutchwork"`).

## Editable install (this repo's venv)

```
$ cd /home/djp/source/clutch && uv run python -I -c 'import importlib.metadata as m ...'
python 3.14.6
version 0.3.0
Project-URL ['Repository, https://github.com/protus75/clutchwork']
dist path /home/djp/source/clutch/.venv/lib/python3.14/site-packages/clutchwork-0.3.0.dist-info
direct_url {"url":"file:///home/djp/source/clutch","dir_info":{"editable":true}}
metadata("clutch") -> PackageNotFoundError No package metadata was found for clutch
```

## Non-editable install (wheel into a throwaway venv)

```
$ S=<scratchpad>/upstream-step0
$ cd /home/djp/source/clutch && uv build --wheel --out-dir $S/dist
Building wheel (uv build backend)...
Successfully built $S/dist/clutchwork-0.3.0-py3-none-any.whl
# git status --porcelain --ignored identical before and after: the build wrote nothing in the repo

$ python3 -I -c '<print Name/Version/Requires-Python/Project-URL lines of the wheel METADATA>'
clutchwork-0.3.0.dist-info/METADATA
Name: clutchwork
Version: 0.3.0
Requires-Python: >=3.14
Project-URL: Repository, https://github.com/protus75/clutchwork

$ uv venv --python 3.14 $S/venv
$ uv pip install --python $S/venv/bin/python $S/dist/clutchwork-0.3.0-py3-none-any.whl
 + pydantic-core==2.50.4  + pyyaml==6.0.3  + typing-extensions==4.16.0  + typing-inspection==0.4.5 ...

$ cd $S/empty && $S/venv/bin/python -I -c 'import importlib.metadata as m ...'
python 3.14.6
version 0.3.0
Project-URL ['Repository, https://github.com/protus75/clutchwork']
dist path $S/venv/lib/python3.14/site-packages/clutchwork-0.3.0.dist-info
direct_url {"url":"file://$S/dist/clutchwork-0.3.0-py3-none-any.whl","archive_info":{}}
clutch imported from $S/venv/lib/python3.14/site-packages/clutch/__init__.py
metadata("clutch") -> PackageNotFoundError No package metadata was found for clutch
```

## The published release on PyPI

```
$ curl -sS -o pypi_clutchwork.json -w '%{http_code}\n' https://pypi.org/pypi/clutchwork/json
200
info: name=clutchwork version=0.2.4 project_urls={'Repository': 'https://github.com/protus75/clutchwork'}
```

## Conclusion

- `importlib.metadata.metadata("clutchwork").get_all("Project-URL")` returns `['Repository, https://github.com/protus75/clutchwork']` in both the editable and the non-editable (wheel) install. PyPI's 0.2.4 release metadata carries the same Repository URL.
- `metadata("clutch")`, as the plan's text has it, raises `PackageNotFoundError` in both installs. The footer's version must use `version("clutchwork")`.
- The parse `value.split(", ", 1)[1]` for `value.startswith("Repository, ")` (the existing reader in `clutch/observe.py::help_payload`) works on this exact string.

## Side finding (not part of the plan; report only, not filed)

`README.md:14` and `clutch/docs/host-contract.md:10` tell hosts to install with `uv add --dev clutch`. On PyPI, `clutch` is an unrelated package:

```
$ curl -sS -o pypi_clutch.json -w '%{http_code}\n' https://pypi.org/pypi/clutch/json
200
info: name=Clutch version=0.1a2 summary='A Python Web Framework for GAE' project_urls={'Homepage': 'http://getclutch.appspot.com', ...}

$ printf 'clutch\n' > req_clutch.in && uv pip compile req_clutch.in --python-version 3.14 --no-header
Resolved 6 packages in 1.30s
clutch==0.1a2
mako==1.4.3 ... routes==2.5.1
```

A host that follows the install docs resolves `clutch==0.1a2` (a GAE web framework), not clutchwork. Separately, `metadata("clutchwork")` then raises in that host, so the verb's Repository lookup would fail there too.
