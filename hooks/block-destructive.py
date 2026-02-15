#!/usr/bin/env python3
"""PreToolUse hook: Block destructive bash commands.

Reads JSON from stdin, checks the command against a blocklist of
dangerous patterns, and returns a deny decision if matched.
"""

import json
import re
import sys


BLOCKED_PATTERNS = [
    # Filesystem destruction
    (r"\brm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f\b.*\s+/\s*$", "rm -rf / (filesystem wipe)"),
    (
        r"\brm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f\b.*\s+/[a-z]+\s*$",
        "rm -rf on system directory",
    ),
    (r"\brm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f\b.*\s+~\s*$", "rm -rf ~ (home directory wipe)"),
    (
        r"\brm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f\b.*\s+\.\s*$",
        "rm -rf . (current directory wipe)",
    ),
    # Disk destruction
    (r"\bdd\b.*\bof=/dev/[sh]d", "dd write to disk device"),
    (r"\bmkfs\b", "filesystem format command"),
    (r"\bfdisk\b", "disk partition command"),
    # Fork bomb
    (r":\(\)\s*\{", "fork bomb"),
    # Dangerous redirects
    (r">\s*/dev/sd[a-z]", "redirect to disk device"),
    (r">\s*/dev/null\s*2>&1\s*<\s*/dev/", "suspicious /dev redirect"),
    # Network exfiltration of sensitive files
    (
        r"\bcurl\b.*(-d|--data).*(/etc/passwd|/etc/shadow|\.env|\.ssh)",
        "exfiltration of sensitive files",
    ),
    (r"\bwget\b.*(-O|-P)\s*-.*\|", "wget pipe execution"),
    # Credential theft
    (r"\bcurl\b.*\|\s*(ba)?sh", "curl pipe to shell (remote code execution)"),
    (r"\bwget\b.*\|\s*(ba)?sh", "wget pipe to shell (remote code execution)"),
    # Git force push to main/master
    (r"\bgit\s+push\s+.*--force.*\b(main|master)\b", "force push to main/master"),
    (r"\bgit\s+push\s+-f\b.*\b(main|master)\b", "force push to main/master"),
    # Git destructive operations without explicit request
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard (destructive)"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f (destructive)"),
    # Windows-specific destructive commands
    (r"\bformat\s+[a-zA-Z]:", "format drive"),
    (r"\bdel\s+/[sS]\s+/[qQ]\s+[cC]:\\", "recursive silent delete on C:"),
    (r"\brd\s+/[sS]\s+/[qQ]\s+[cC]:\\", "recursive silent remove on C:"),
    # Environment variable manipulation
    (r"\bsetx?\b.*\bPATH\b.*=\s*$", "PATH wipe"),
    # Shutdown/reboot
    (r"\bshutdown\b", "system shutdown"),
    (r"\breboot\b", "system reboot"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"BLOCKED: {description}. "
                        f"Command '{command[:80]}...' matches destructive pattern. "
                        "If you need this command, ask the user to run it manually."
                    ),
                }
            }
            json.dump(result, sys.stdout)
            sys.exit(0)

    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
