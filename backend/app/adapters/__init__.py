"""Hackathon adapter layer (Open Agent 2026, Wildcard [Tinkerer]).

The core application never imports sponsor SDKs directly. Everything external
arrives as Evidence through one of these adapters, so the new work stays
isolated, testable and switchable with HACKATHON_MODE.
"""
from app.adapters.base import AdapterError, Evidence, QuerySpec, SourceAdapter, dedupe

__all__ = ["AdapterError", "Evidence", "QuerySpec", "SourceAdapter", "dedupe"]
