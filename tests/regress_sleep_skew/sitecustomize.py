"""Reproduce a load-induced inversion of short sleeps."""

import time

_sleep = time.sleep


def skewed_sleep(seconds):
    _sleep(seconds + 0.2 if seconds < 0.15 else seconds)


time.sleep = skewed_sleep
