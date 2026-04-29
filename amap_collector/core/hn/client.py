from typing import Optional, Self
import requests

import amap_collector.core.hn.validations as validations

HN_CLIENT_LABEL: str = 'hn'

class HnAmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class HnAmapClient:
    pass
