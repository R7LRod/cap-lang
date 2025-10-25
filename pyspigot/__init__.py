import threading
import time


class Bukkit:
    @staticmethod
    def getName():
        return "PySpigot Server"


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
