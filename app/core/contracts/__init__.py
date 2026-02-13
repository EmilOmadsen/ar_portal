"""
Contract generation and management module
"""
# Import functions directly for convenience
from .loader import load_template
from .builder.builder import build_context
from .exporter import render_contract
from .validation import validate_contract_data

__all__ = [
    "load_template",
    "build_context",
    "render_contract",
    "validate_contract_data",
]
