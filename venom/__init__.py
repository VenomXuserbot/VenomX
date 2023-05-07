# init
import inspect
from sys import version_info as ver
from typing import Any

from .x import VenomX_
from .config import Config, SecureConfig
from .db import Collection
from .logger import logging
from .core.types.message import MyMessage
from .core.command_manager import manager
from .core.client import Venom
from .helpers import plugin_name

python_ver = f"v{ver[0]}.{ver[1]}.{ver[2]}"


def test_print(message: Any):
    inspect_ = inspect.stack()[1]
    filename = inspect_.filename
    line_number = inspect_.lineno
    print(f"#--- {filename} - {line_number} ---#\n{message}")


venom = Venom()
