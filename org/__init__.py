"""Compatibility package to allow `from org.bukkit import ...` imports.
This package re-exports symbols from the local `pyspigot` shim so compiled
CapLang plugins that use Java-style imports continue to work in Python.
"""

# Intentionally left blank - subpackages provide the Python shims.
