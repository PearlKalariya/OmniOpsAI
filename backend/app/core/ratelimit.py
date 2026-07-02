"""Shared rate limiter (in-memory, per-IP).

In-memory storage resets on restart and is per-process — fine for a single
dev/demo instance. Swap to Redis storage when running multiple workers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
