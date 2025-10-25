import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspigot import Bukkit
from pyspigot import Scheduler
print('LagManager plugin (CapLang)')
def monitor():
    print('[LagManager] Checking server...')
    print(Bukkit.getName())
def on_enable():
    print('[LagManager] Enabled')
    Scheduler.schedule_repeating(monitor, 2.0)
on_enable()