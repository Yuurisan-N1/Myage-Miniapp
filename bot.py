import os
import sys
import json
import time
import uuid
import signal
import asyncio
import aiohttp

from utils.banner import show_banner

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

MY_PROJECT = "My Age Miniapp"
BASE_URL = "https://myageapp.xyz"


def clean_text(value, fallback):
    text = str(value)
    for symbol in "[]|#!@$%^&*()-":
        text = text.replace(symbol, " ")
    text = " ".join(text.split())
    return text if text else fallback


def log_green(msg):
    print(f"{GREEN}{BOLD}{msg}{RESET}", flush=True)


def log_yellow(msg):
    print(f"{YELLOW}{BOLD}{msg}{RESET}", flush=True)


def log_red(msg):
    print(f"{RED}{BOLD}{msg}{RESET}", flush=True)


def plural(count, word):
    return word if int(count) == 1 else word + "s"


def mask_proxy(proxy_url):
    try:
        value = proxy_url.split("://")[-1]
        after_at = value.split("@")[-1]
        host_part = after_at.split(":")[0]
        port_part = after_at.split(":")[1] if ":" in after_at else ""
        octets = host_part.split(".")
        if len(octets) == 4:
            masked_host = f"{octets[0]}*****{octets[3]}"
        elif len(host_part) > 4:
            masked_host = f"{host_part[:2]}*****{host_part[-2:]}"
        else:
            masked_host = "***"
        suffix = f":{port_part}" if port_part else ""
        return f"http://user:pass@{masked_host}{suffix}"
    except Exception:
        return "http://user:pass@***:***"


def signal_handler(sig, frame):
    print(f"\r\033[K", end="", flush=True)
    log_red("Script stopped by user")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def format_duration(seconds):
    left = int(max(seconds, 0))
    days, rest = divmod(left, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, seconds = divmod(rest, 60)
    if days > 0:
        return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


async def countdown(seconds, label):
    left = int(max(seconds, 0))
    if left < 1:
        return
    text = clean_text(label, "Next cycle")
    try:
        while left > 0:
            print(f"\r{YELLOW}{BOLD}{text} {format_duration(left)}{RESET}", end="", flush=True)
            await asyncio.sleep(1)
            left -= 1
    finally:
        print(f"\r{' ' * 70}\r", end="", flush=True)


def load_config():
    with open("config.json", "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return int(data["settings"]["sleep_seconds"])


def load_lines(name):
    if not os.path.exists(name):
        return []
    with open(name, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


class Account:
    def __init__(self, init_data, proxy, line):
        self.init_data = init_data
        self.proxy = proxy
        self.line = line

    async def api(self, session, path, body=None):
        headers = {
            "authorization": "tma " + self.init_data,
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
            ),
            "accept": "application/json",
            "origin": BASE_URL,
            "referer": BASE_URL + "/",
        }
        if body is not None:
            headers["content-type"] = "application/json"
            headers["idempotency-key"] = str(uuid.uuid4())
        for attempt in range(3):
            try:
                async with session.request(
                    "POST" if body is not None else "GET",
                    f"{BASE_URL}/api/{path}",
                    json=body,
                    headers=headers,
                    proxy=self.proxy,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as reply:
                    try:
                        data = await reply.json(content_type=None)
                    except Exception:
                        data = {}
                    return reply.status, data if isinstance(data, dict) else {}
            except Exception:
                if attempt == 2:
                    return 0, {}
                await asyncio.sleep(2 * (attempt + 1))
        return 0, {}


async def claim_tasks(account, session):
    status, data = await account.api(session, "tasks")
    if status != 200:
        log_red("The task list could not be read from the server")
        return
    waiting = [task for task in data.get("tasks", []) if not task.get("done")]
    channels = [task for task in waiting if task.get("kind") == "channel"]
    presses = [task for task in waiting if task.get("kind") != "channel"]
    if channels:
        log_yellow(
            f"Channel tasks still waiting for a manual join are {len(channels)}"
        )
    if not presses:
        log_yellow("Every available task was already claimed for this account")
        return
    for task in presses:
        title = clean_text(task.get("title"), clean_text(task.get("id"), "task"))
        required = int(task.get("pressesRequired") or 1)
        pressed = int(task.get("presses") or 0)
        for _ in range(max(0, required - pressed)):
            status, _ = await account.api(session, "tasks", {"taskId": task.get("id")})
            if status != 200:
                break
        if status == 200:
            reward = int(task.get("reward") or 0)
            log_green(f"Task {title} credited {reward} AGE")
        elif status in (400, 409):
            log_yellow(f"Task {title} was already claimed earlier")
        else:
            log_red(f"Task {title} was refused by the server")


async def run_account(account, index):
    async with aiohttp.ClientSession() as session:
        if account.proxy:
            log_yellow(f"Using proxy {mask_proxy(account.proxy)}")

        status, data = await account.api(session, "session", {})
        if status == 401:
            log_red(
                f"Account on line {account.line} holds invalid initData and was skipped"
            )
            return
        if status != 200:
            log_red("The account state could not be read from the server")
            return

        user = data.get("user") or {}
        name = clean_text(user.get("username") or user.get("name"), "Unknown")
        log_green(f"Signed in {name} with {int(user.get('points') or 0)} AGE")

        welcome = data.get("welcome") or {}
        if welcome and not welcome.get("claimed"):
            status, body = await account.api(session, "welcome", {})
            if status == 200:
                log_green(f"Welcome bonus credited {int(body.get('total') or 0)} AGE")
            else:
                log_red("The welcome bonus was refused by the server")

        daily = data.get("daily") or {}
        if daily.get("ready"):
            status, body = await account.api(session, "daily", {})
            if status == 200:
                log_green(
                    f"Daily check in credited {int(body.get('reward') or 0)} AGE "
                    f"on streak day {int(body.get('streak') or 0)}"
                )
            else:
                log_red("The daily check in was refused by the server")
        else:
            log_yellow("Daily check in was already claimed today")

        spin = data.get("spin") or {}
        if spin.get("ready"):
            status, body = await account.api(session, "spin", {})
            if status == 200:
                if body.get("kind") == "gram":
                    log_green(f"Spin wheel credited {body.get('amount')} GRAM")
                elif body.get("kind") == "pass":
                    log_green("Spin wheel credited a pass to this account")
                else:
                    log_green(f"Spin wheel credited {int(body.get('amount') or 0)} AGE")
            else:
                log_red("The spin wheel was refused by the server")
        else:
            log_yellow("The lucky spin is still on cooldown for this account")

        mystery = data.get("mystery") or {}
        for _ in range(int(mystery.get("left") or 0)):
            status, body = await account.api(session, "mystery", {})
            if status != 200:
                log_red("The mystery box was refused by the server")
                break
            if body.get("kind") == "gram":
                log_green(f"Mystery box credited {body.get('amount')} GRAM")
            elif body.get("kind") == "pass":
                log_green("Mystery box credited a pass to this account")
            else:
                log_green(f"Mystery box credited {int(body.get('amount') or 0)} AGE")
        if not int(mystery.get("left") or 0):
            log_yellow("No mystery card was available to open for this account")

        vault = data.get("vault") or {}
        if vault:
            now = int(data.get("serverNow") or 0)
            started = int(vault.get("startedAt") or now)
            span = min(max(now - started, 0), int(vault.get("hours") or 0) * 3600000)
            ready = int(vault.get("perHour") or 0) * span // 3600000
            before = int(user.get("points") or 0)
            if ready > 0:
                status, body = await account.api(session, "vault", {})
                if status == 200:
                    log_green(
                        f"Vault balance rose from {before} to {int(body.get('points') or 0)} AGE"
                    )
                else:
                    log_red("The vault claim was refused by the server")
            else:
                log_yellow("Vault balance stayed unchanged after this run")

        status, data = await account.api(session, "achievements")
        paid = 0
        if status == 200:
            for item in data.get("list", []):
                if not item.get("done") or item.get("claimed"):
                    continue
                status, _ = await account.api(
                    session, "achievements", {"key": item.get("key")}
                )
                if status == 200:
                    paid += 1
        if paid:
            verb = "was" if paid == 1 else "were"
            log_green(f"{paid} {plural(paid, 'achievement')} {verb} paid on this account")
        else:
            log_yellow("No achievement has reached its target for this account yet")

        await claim_tasks(account, session)

        status, data = await account.api(session, "session", {})
        if status == 200:
            total = int((data.get("user") or {}).get("points") or 0)
            log_green(f"Cycle closed with a balance of {total} AGE")


async def main():
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.reconfigure(line_buffering=True)
    try:
        show_banner(MY_PROJECT)
    except Exception:
        pass

    sleep_seconds = load_config()
    lines = load_lines("data.txt")
    proxies = load_lines("proxy.txt")

    if not lines:
        log_red("File data.txt is empty and holds no initData string")
        return

    accounts = [
        Account(raw, proxies[i % len(proxies)] if proxies else None, i + 1)
        for i, raw in enumerate(lines)
    ]

    cycle = 0
    while True:
        cycle += 1
        log_yellow(f"Starting automation cycle number {cycle}")
        for i, account in enumerate(accounts):
            if i:
                print(flush=True)
            await run_account(account, i + 1)
        await countdown(sleep_seconds, "Next cycle starts in")
        try:
            show_banner(MY_PROJECT)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\r\033[K", end="", flush=True)
        log_red("Script stopped by user")