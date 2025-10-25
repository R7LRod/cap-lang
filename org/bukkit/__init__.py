"""Shim for org.bukkit that re-exports from pyspigot.

Allows `from org.bukkit import Bukkit, Scheduler, getServer` in generated code.
"""
from pyspigot import Bukkit, Scheduler, getServer, getBukkitServer

__all__ = ["Bukkit", "Scheduler", "getServer", "getBukkitServer"]
