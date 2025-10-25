import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspigot import Bukkit
print('PySpigot/Bukkit demo')
print(Bukkit.getName())