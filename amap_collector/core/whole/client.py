from typing import Optional, Self
import requests

import amap_collector.core.whole.validations as validations
from amap_collector.core.whole.endpoint import WholeAmapList

WHOLE_CLIENT_LABEL: str = 'whole'

class WholeAmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class WholeAmapClient:
    pass
