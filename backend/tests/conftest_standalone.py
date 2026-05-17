"""
Pytest configuration for standalone agent tests.
This conftest patches the prisma module system-wide BEFORE any application imports.
"""
import sys
from unittest.mock import MagicMock

import pytest

mock_prisma_module = MagicMock()
mock_prisma_module.prisma = MagicMock()
mock_prisma_module.prisma.is_connected = True
sys.modules['prisma'] = mock_prisma_module
sys.modules['app.prisma'] = mock_prisma_module