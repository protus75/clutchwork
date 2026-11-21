"""Reproduce a load-induced inversion of short sleeps."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce load-induced inversion of short sleeps
# relates: []
# owner: engine
# verified: 75d75946
# hash: 4dca85e0e33f348469b2d48d759e2777a986cfce2c46d8febc0d6267bc4cb8a2

import time

_sleep = time.sleep


def skewed_sleep(seconds):
    _sleep(seconds + 0.2 if seconds < 0.15 else seconds)


time.sleep = skewed_sleep
