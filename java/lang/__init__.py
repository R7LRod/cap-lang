"""Shim for java.lang used by compiled plugins.

Provides a minimal System.gc() implementation that maps to Python's gc.collect().
"""
import gc

class System:
    @staticmethod
    def gc():
        try:
            gc.collect()
        except Exception:
            pass

__all__ = ["System"]
