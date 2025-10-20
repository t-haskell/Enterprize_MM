"""Shared application dependencies for the API service."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Centralised rate limiter instance reused across routers so per-client budgets
# are accounted for globally. The limiter can be configured via environment
# variables if needed (see docs/DEVELOPER_GUIDE.md for details).
limiter = Limiter(key_func=get_remote_address)
