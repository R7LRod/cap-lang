# --------------------
# Lightweight Lag Management
# For R7L Suite. mc.r7l.org
# --------------------

import pyspigot as ps
from org.bukkit import Bukkit
from java.lang import System
from org.bukkit.entity import Item, ExperienceOrb
import time

# --------------------
# Configuration
# --------------------
CHECK_INTERVAL_TICKS = 100        # check every 30 seconds
INITIAL_DELAY_TICKS = 20          # start after 1 second
TPS_THRESHOLD = 16.0              # below this triggers cleanup
MIN_TPS_TO_SKIP = 19.5            # if TPS is high, skip mitigation

CLEAR_ENTITY_CLASSES = (Item, ExperienceOrb)
VERBOSE = True
ADMIN_PERMISSION = "lagmanager.admin"

# State
last_tps = None
last_mitigation = None

task_mgr = ps.task_manager()
cmd_mgr = ps.command_manager()


# --------------------
# Helpers
# --------------------
def now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def log(msg):
    Bukkit.getConsoleSender().sendMessage("[LagManager] " + msg)

def get_tps_values():
    server = Bukkit.getServer()
    try:
        if hasattr(server, "getTPS"):
            arr = server.getTPS()
            return [float(x) for x in arr]
    except Exception:
        pass
    try:
        if hasattr(server, "getTickTimes"):
            times = server.getTickTimes()
            if not times or len(times) == 0:
                return [20.0]
            total = 0.0
            count = 0
            for t in times:
                if t > 0:
                    total += float(t)
                    count += 1
            if count == 0:
                return [20.0]
            avg_nanos = total / count
            tps = min(20.0, 1e9 / avg_nanos)
            return [tps]
    except Exception:
        pass
    return [0.0]

def clear_entities():
    removed = 0
    for world in Bukkit.getWorlds():
        for ent in list(world.getEntities()):
            for klass in CLEAR_ENTITY_CLASSES:
                try:
                    if klass.isInstance(ent):
                        ent.remove()
                        removed += 1
                        break
                except Exception:
                    continue
    return removed

def run_mitigation(reason="auto"):
    global last_mitigation
    try:
        System.gc()
    except Exception:
        pass
    removed = 0
    try:
        removed = clear_entities()
    except Exception as e:
        log("Error clearing entities: " + str(e))
    last_mitigation = {
        "time": now_ts(),
        "reason": reason,
        "removed": removed
    }
    if VERBOSE:
        log("Mitigation run (reason=%s) - removed %d entities" % (reason, removed))


def tps_check_task():
    global last_tps
    tps_vals = get_tps_values()
    last_tps = {"time": now_ts(), "tps": tps_vals}
    current_tps = tps_vals[0] if tps_vals else 0.0
    if current_tps >= MIN_TPS_TO_SKIP:
        return
    if current_tps < TPS_THRESHOLD:
        run_mitigation("tps_below_%.2f" % TPS_THRESHOLD)


def tps_command(sender, label, args):
    def is_admin():
        try:
            return sender.isOp() or sender.hasPermission(ADMIN_PERMISSION)
        except Exception:
            return True

    if len(args) == 0:
        if last_tps is None:
            sender.sendMessage("TPS: unknown")
        else:
            sender.sendMessage("TPS (sample): " + ", ".join("%.2f" % v for v in last_tps["tps"]))
            sender.sendMessage("Last check: " + last_tps["time"])
        if last_mitigation is not None:
            sender.sendMessage(
                "Last mitigation: %s | removed=%d | reason=%s" %
                (last_mitigation["time"], last_mitigation["removed"], last_mitigation["reason"])
            )
        return True

    sub = args[0].lower()
    if sub == "gc":
        if not is_admin():
            sender.sendMessage("You don't have permission.")
            return True
        run_mitigation("manual_gc_by_" + sender.getName())
        sender.sendMessage("Manual GC & entity clear triggered.")
        return True

    if sub == "clear":
        if not is_admin():
            sender.sendMessage("You don't have permission.")
            return True
        removed = clear_entities()
        sender.sendMessage("Cleared dropped items/xp: %d removed" % removed)
        return True

    if sub == "threshold":
        if not is_admin():
            sender.sendMessage("You don't have permission.")
            return True
        if len(args) < 2:
            sender.sendMessage("Usage: /tpsinfo threshold <value>")
            return True
        try:
            val = float(args[1])
            global TPS_THRESHOLD
            TPS_THRESHOLD = val
            sender.sendMessage("TPS threshold set to %.2f" % val)
        except Exception:
            sender.sendMessage("Invalid number.")
        return True

    sender.sendMessage("Unknown subcommand. Usage: /tpsinfo [gc|clear|threshold <value>]")
    return True


try:
    task_mgr.scheduleRepeatingTask(tps_check_task, INITIAL_DELAY_TICKS, CHECK_INTERVAL_TICKS, None)
    log("Scheduled TPS check every %d ticks" % CHECK_INTERVAL_TICKS)
except Exception as e:
    log("Failed to schedule task: " + str(e))

try:
    def safe_tps_command(*args):
        if len(args) == 4:
            sender, command, label, arguments = args
        else:
            sender, label, arguments = args
        return tps_command(sender, label, arguments)

    cmd = cmd_mgr.registerCommand(safe_tps_command, "tpsinfo", "Show TPS and manage mitigations")
    cmd.setAliases(["lag", "lagmgr"])
    log("Registered /tpsinfo command")
except Exception as e:
    log("Failed to register command: " + str(e))
