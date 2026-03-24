#!/usr/bin/env python3
import logging
import psutil

logger = logging.getLogger(__name__)


def find_processes_on_port(port: int) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for conn in proc.net_connections(kind="inet"):
                if conn.laddr.port == port:
                    matches.append((proc.pid, proc.name()))
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return matches


def kill_process(pid: int) -> bool:
    try:
        proc = psutil.Process(pid)
        proc.kill()
        proc.wait(timeout=5)
        return True
    except psutil.NoSuchProcess:
        return True
    except (psutil.AccessDenied, psutil.TimeoutExpired) as e:
        logger.error(f"Could not kill PID {pid}: {e}")
        return False


def free_port(port: int) -> None:
    if not (1 <= port <= 65535):
        logger.error(f"Invalid port number: {port}. Must be between 1 and 65535.")
        return

    logger.info(f"Scanning for processes on port {port}...")
    processes = find_processes_on_port(port)

    if not processes:
        logger.warning(f"No process found listening on port {port}.")
        return

    for pid, name in processes:
        logger.info(f"Found '{name}' (PID {pid})")
        success = kill_process(pid)
        if success:
            logger.info(f"Killed '{name}' (PID {pid}) — port {port} is now free.")
        else:
            logger.error(
                f"Failed to kill '{name}' (PID {pid}). Try running as administrator/root."
            )


if __name__ == "__main__":
    free_port(3000)
