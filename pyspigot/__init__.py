import threading
import time


class Bukkit:
    @staticmethod
    def getName():
        return "PySpigot Server"
    
    @staticmethod
    def getConsoleSender():
        return ConsoleSender()

    @staticmethod
    def getServer():
        return _server


class Scheduler:
    @staticmethod
    def schedule_repeating(func, interval_seconds: float):
        """Schedule a repeating callable in a daemon thread."""

        def runner():
            try:
                while True:
                    try:
                        func()
                    except Exception as e:
                        print(f"Scheduled task error: {e}")
                    time.sleep(interval_seconds)
            except Exception:
                pass

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        return t


# Export symbols expected by compiled examples
Bukkit = Bukkit
Scheduler = Scheduler


class _TaskManager:
    def scheduleRepeatingTask(self, func, initial_delay_ticks, interval_ticks, _):
        # Convert ticks to seconds (20 ticks = 1 second)
        try:
            interval = float(interval_ticks) / 20.0
        except Exception:
            interval = 1.0

        def wrapper():
            # optionally honor initial delay (in seconds)
            try:
                time.sleep(float(initial_delay_ticks) / 20.0)
            except Exception:
                pass
            return Scheduler.schedule_repeating(func, interval)

        # Start wrapper in a daemon thread to not block
        t = threading.Thread(target=wrapper, daemon=True)
        t.start()
        return t


def task_manager():
    return _TaskManager()


class _Command:
    def __init__(self, func, name, desc):
        self.func = func
        self.name = name
        self.desc = desc

    def setAliases(self, aliases):
        self.aliases = aliases
        return self


class _CommandManager:
    def registerCommand(self, func, name, desc):
        return _Command(func, name, desc)


def command_manager():
    return _CommandManager()


# minimal server/world/entity simulation
class Item:
    @staticmethod
    def isInstance(obj):
        return isinstance(obj, Item)


class ExperienceOrb:
    @staticmethod
    def isInstance(obj):
        return isinstance(obj, ExperienceOrb)


class Entity:
    def remove(self):
        pass


class World:
    def __init__(self):
        self._entities = []

    def getEntities(self):
        return list(self._entities)

    def addEntity(self, ent):
        self._entities.append(ent)


class Server:
    def __init__(self):
        self._worlds = [World()]

    def getWorlds(self):
        return self._worlds

    def getTPS(self):
        return [20.0]

    def getTickTimes(self):
        return []


_server = Server()

def getServer():
    return _server

def getBukkitServer():
    return _server


class ConsoleSender:
    def sendMessage(self, msg: str):
        print(msg)
