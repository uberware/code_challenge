"""
Simple asset management service.
"""

import logging
import sys

# it would be better to have a standard logging package but for this sample
# we set up some reasonable basic logging
logger = logging.getLogger("asset_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# directly specify the what gets exported from this module
__all__ = ["logger"]
