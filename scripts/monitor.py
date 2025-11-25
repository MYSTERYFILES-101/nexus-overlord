#!/usr/bin/env python3
"""
NEXUS OVERLORD - Live Monitor Script
Beobachtet server.log und meldet Fehler sofort
"""

import subprocess
import re
import sys
from datetime import datetime

# Farben fuer Terminal
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Fehler-Pattern
ERROR_PATTERNS = [
    (r'ERROR', 'ERROR'),
    (r'Exception', 'EXCEPTION'),
    (r'Traceback', 'TRACEBACK'),
    (r'500 Internal Server Error', '500 ERROR'),
    (r'404 Not Found', '404 ERROR'),
    (r'KeyError', 'KEY ERROR'),
    (r'TypeError', 'TYPE ERROR'),
    (r'AttributeError', 'ATTR ERROR'),
    (r'sqlite3\.Error', 'DB ERROR'),
    (r'ConnectionError', 'CONNECTION ERROR'),
    (r'TimeoutError', 'TIMEOUT'),
]

# Request-Pattern
REQUEST_PATTERN = re.compile(r'"(GET|POST|PUT|DELETE) ([^"]+)" (\d+)')

def analyze_line(line):
    """Analysiert eine Log-Zeile"""
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Check for errors
    for pattern, error_type in ERROR_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            print(f"\n{RED}{'='*60}")
            print(f"[{timestamp}] {error_type} GEFUNDEN!")
            print(f"{'='*60}{RESET}")
            print(f"{YELLOW}{line.strip()}{RESET}")
            print(f"{RED}{'='*60}{RESET}\n")
            return 'error'

    # Check for requests
    match = REQUEST_PATTERN.search(line)
    if match:
        method, path, status = match.groups()
        status_int = int(status)

        if status_int >= 500:
            color = RED
            symbol = '❌'
        elif status_int >= 400:
            color = YELLOW
            symbol = '⚠️'
        elif status_int >= 300:
            color = BLUE
            symbol = '↪️'
        else:
            color = GREEN
            symbol = '✅'

        print(f"{color}[{timestamp}] {symbol} {method} {path} -> {status}{RESET}")
        return 'request'

    # Info messages
    if 'INFO' in line:
        # Nur wichtige Info-Meldungen anzeigen
        if any(x in line for x in ['Starting', 'Running', 'Loaded', 'Connected']):
            print(f"{BLUE}[{timestamp}] ℹ️  {line.strip()[-80:]}{RESET}")
        return 'info'

    return None

def main():
    print(f"""
{GREEN}{'='*60}
🔍 NEXUS OVERLORD - LIVE MONITOR
{'='*60}{RESET}

{BLUE}Beobachte: /home/nexus/nexus-overlord/logs/server.log{RESET}
{YELLOW}Druecke Ctrl+C zum Beenden{RESET}

{GREEN}Legende:{RESET}
  ✅ = OK (2xx)
  ↪️ = Redirect (3xx)
  ⚠️ = Client Error (4xx)
  ❌ = Server Error (5xx)

{GREEN}Warte auf Requests...{RESET}
""")

    # SSH tail -f command
    cmd = [
        'sshpass', '-p', 'MarNat14223+',
        'ssh', '-o', 'StrictHostKeyChecking=no',
        'root@116.203.191.160',
        'tail -f /home/nexus/nexus-overlord/logs/server.log'
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        error_count = 0
        request_count = 0

        for line in process.stdout:
            result = analyze_line(line)
            if result == 'error':
                error_count += 1
            elif result == 'request':
                request_count += 1

    except KeyboardInterrupt:
        print(f"\n\n{GREEN}{'='*60}")
        print(f"Monitor beendet")
        print(f"{'='*60}")
        print(f"Requests beobachtet: {request_count}")
        print(f"Fehler gefunden: {error_count}")
        print(f"{'='*60}{RESET}\n")

    except Exception as e:
        print(f"{RED}Monitor Fehler: {e}{RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()
