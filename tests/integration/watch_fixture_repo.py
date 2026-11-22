# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Re-exports watch_fixture_repo from tests/config_helpers.py for snapshot integration tests.
# relates: [tests/integration/test_config.py]
# owner: tests/integration/test_config.py
# verified: 38957300
# hash: 3cfae559a60813bab8e3705ff459d906f75b08c889ac7edf273a3a0fecde2a11

from tests.config_helpers import watch_fixture_repo  # noqa: F401
