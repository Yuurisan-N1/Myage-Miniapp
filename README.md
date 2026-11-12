<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=My%20Age%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=Multi-Account%20Automation%20Client%20for%20My%20Age%20Miniapp&descAlign=50&descAlignY=58"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Auto+Daily+Check-in+%7C+Streak+Tracked;Auto+Spin+Wheel+%7C+Vault+Claim;Auto+Mystery+Box+%7C+Achievement+Claim;Auto+Task+Claiming+%7C+Multi-Account"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.12+-3776ab?logo=python&logoColor=white"/>
  <img alt="platform" src="https://img.shields.io/badge/Platform-My%20Age%20Miniapp-111111"/>
  <img alt="multi-account" src="https://img.shields.io/badge/Multi--Account-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>My Age Miniapp Bot</b> is a multi-account automation client for the My Age Miniapp platform.<br/>
  It reads Telegram initData from a plain text file, signs in each account, and on every cycle claims the welcome bonus, daily check-in, spin wheel, mystery boxes, vault balance, achievements, and tasks, then sleeps until the next cycle, all across multiple accounts with proxy support.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Getting initData](#getting-initdata)
- [Running the Bot](#running-the-bot)
- [Features](#features)
- [File Structure](#file-structure)
- [Disclaimer](#disclaimer)

---

## Requirements

- Python 3.12
- pip
- Git

---

## Installation

### Install Python

**Windows:**

1. Download the installer from https://www.python.org/downloads/ and run it
2. On the first screen tick **Add python.exe to PATH**, then continue with the default options
3. Open Command Prompt and verify:

```cmd
python --version
```

**Linux (Ubuntu / Debian):**

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip
python3 --version
```

**macOS:**

```bash
brew install python
python3 --version
```

> If you do not have Homebrew, install it first from https://brew.sh

**Termux (Android):**

```bash
pkg update && pkg upgrade -y
pkg install python git -y
python --version
```

---

### Clone and Install

**Clone the repository:**

```bash
git clone https://github.com/Yuurisan-N1/Myage-Miniapp.git
cd Myage-Miniapp
```

**Install dependencies:**

```bash
pip install aiohttp yuurisan
```

---

## Configuration

### 1. Accounts (data.txt)

Fill `data.txt` with one Telegram initData string per line. Blank lines are ignored:

```
query_id=AAH...&user=...&auth_date=...&hash=...
query_id=AAH...&user=...&auth_date=...&hash=...
```

### 2. Proxy (proxy.txt)

Fill `proxy.txt` with proxies, one per line (optional, leave empty to connect directly):

```
http://user:pass@host:port
socks5://user:pass@host:port
```

Proxies are paired to accounts by index. If there are fewer proxies than accounts, they wrap around.

### 3. Bot Settings (config.json)

`sleep_seconds` controls how many seconds the bot waits between cycles. The default is 3600 (one hour).

---

## Getting initData

1. Open Telegram and launch the My Age Miniapp.
2. Open the browser developer tools (F12) and go to the Network tab.
3. Look for a request to `myageapp.xyz/api/session`.
4. Copy the value of the `authorization` header after the `tma ` prefix.
5. Paste it as a line in `data.txt`.

The initData expires after a while. If the bot logs `Account on line N holds invalid initData and was skipped`, refresh the initData from the app.

---

## Running the Bot

**Linux / macOS / Termux:**

```bash
python bot.py
```

**Windows:**

```cmd
python bot.py
```

Press `Ctrl+C` once to stop the bot cleanly.

**Run in background with screen (Linux / macOS / Termux):**

```bash
screen -S myage
python bot.py
```

Detach with `Ctrl+A` then `D`. Reattach anytime:

```bash
screen -r myage
```

---

## Features

### Auto Welcome Bonus
If an account has an unclaimed welcome bonus, it is claimed at the start of the first cycle.

### Auto Daily Check-in
The bot claims the daily check-in reward each cycle. If already claimed today, it is skipped with a note. The current streak day is logged on each successful claim.

### Auto Spin Wheel
If the spin wheel is ready, the bot spins it and logs the reward. AGE, GRAM, and pass rewards are all handled. If the spin is on cooldown, it is skipped.

### Auto Mystery Box
All available mystery card opens are claimed per cycle. AGE, GRAM, and pass rewards are logged individually. If no card is available, it is skipped.

### Auto Vault Claim
The bot calculates how much AGE has accumulated in the vault since the last claim and claims it. If nothing has accumulated yet, it is skipped.

### Auto Achievement Claim
Completed but unclaimed achievements are claimed each cycle. The total number of achievements paid is logged.

### Auto Task Claiming
Non-channel tasks are completed and claimed automatically. Channel tasks (which require a manual join) are listed but not attempted. Already claimed tasks are skipped.

### Multi Account
All accounts in `data.txt` are processed sequentially within every cycle. Each account uses its own proxy from the pool.

### Proxy Support
Proxies are loaded from `proxy.txt`. HTTP and SOCKS5 are both supported. Proxy credentials are masked in log output. Running without proxies is fully supported.

### Auto Countdown
After all accounts complete a cycle, the bot displays a live `HH:MM:SS` countdown until the next cycle starts.

---

## File Structure

```text
Myage-Miniapp/
├── utils/
│   ├── __init__.py                      # Package marker
│   └── banner.py                        # Banner and terminal title via yuurisan
├── bot.py                               # Main script: sign-in, all claim steps, cycle loop
├── config.json                          # Sleep duration setting
├── data.txt                             # initData strings, one per line
├── proxy.txt                            # Proxy list (optional)
├── LICENSE                              # GNU AGPL v3.0
└── README.md                            # This file
```

---

## Disclaimer

This tool is built for educational and technical exploration purposes. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>