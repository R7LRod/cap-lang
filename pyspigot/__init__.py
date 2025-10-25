class Bukkit:
    @staticmethod
    def getName():
        return "PySpigot Server"

# Export Bukkit at package level to mimic `from pyspigot import Bukkit`
Bukkit = Bukkit
