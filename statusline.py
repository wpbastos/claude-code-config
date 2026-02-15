#!/usr/bin/env python3
"""Claude Code status line: model, git branch, context bar, tokens, duration."""
import json
import os
import re
import subprocess
import sys
import time

CACHE_FILE = os.path.join(os.environ.get("TEMP", "/tmp"), "claude-statusline-git-cache")
CACHE_MAX_AGE = 5  # seconds

# ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def get_git_info():
    """Get git branch and file counts, with caching."""
    try:
        stale = True
        if os.path.exists(CACHE_FILE):
            age = time.time() - os.path.getmtime(CACHE_FILE)
            if age < CACHE_MAX_AGE:
                stale = False

        if stale:
            subprocess.check_output(
                ["git", "rev-parse", "--git-dir"],
                stderr=subprocess.DEVNULL,
            )
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            staged = subprocess.check_output(
                ["git", "diff", "--cached", "--numstat"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            modified = subprocess.check_output(
                ["git", "diff", "--numstat"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            staged_n = len(staged.split("\n")) if staged else 0
            modified_n = len(modified.split("\n")) if modified else 0
            with open(CACHE_FILE, "w") as f:
                f.write(f"{branch}|{staged_n}|{modified_n}")
        else:
            with open(CACHE_FILE) as f:
                parts = f.read().strip().split("|")
                if len(parts) == 3:
                    branch, staged_n, modified_n = parts[0], int(parts[1]), int(parts[2])
                else:
                    return None

        if branch:
            status = ""
            if staged_n > 0:
                status += f" {GREEN}+{staged_n}{RESET}"
            if modified_n > 0:
                status += f" {YELLOW}~{modified_n}{RESET}"
            return f"{branch}{status}"
    except Exception:
        pass
    return None


def main():
    # Fix Windows encoding for Unicode characters (progress bar, ANSI colors)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Show initial status line before first prompt
        current_dir = os.getcwd()
        try:
            git_root = subprocess.check_output(
                ["git", "-C", current_dir, "rev-parse", "--show-toplevel"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
            repo_name = os.path.basename(git_root)
            directory = repo_name if current_dir == git_root else os.path.basename(current_dir)
        except Exception:
            directory = os.path.basename(current_dir)

        git = get_git_info()
        line1 = f"\033[37m[Claude Code]{RESET} \033[94m{directory}{RESET}"
        if git:
            line1 += f" {DIM}│{RESET} \033[96m{git}{RESET}"

        print(line1)
        print(f"{DIM}Ready{RESET}")
        return

    # Model — shorten "Claude 3.5 Opus" → "Opus"
    model_full = data.get("model", {}).get("display_name", "?")
    model = re.sub(r"^Claude\s+[\d.]+\s*", "", model_full)
    model = re.sub(r"^Claude\s+", "", model)

    # Directory — repo-root aware
    current_dir = data.get("workspace", {}).get("current_dir", "")
    try:
        git_root = subprocess.check_output(
            ["git", "-C", current_dir, "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        repo_name = os.path.basename(git_root)
        directory = repo_name if current_dir == git_root else os.path.basename(current_dir)
    except Exception:
        directory = os.path.basename(current_dir)

    # Context % — fallback chain: remaining_percentage → token math → used_percentage → 0
    ctx = data.get("context_window", {})
    remaining = ctx.get("remaining_percentage")
    if remaining is not None:
        pct = int(100 - remaining)
    elif (ctx.get("context_window_size") or 0) > 0:
        usage = ctx.get("current_usage", {})
        tokens = (
            (usage.get("input_tokens") or 0)
            + (usage.get("cache_creation_input_tokens") or 0)
            + (usage.get("cache_read_input_tokens") or 0)
        )
        pct = int(tokens * 100 / ctx["context_window_size"])
    else:
        pct = int(ctx.get("used_percentage") or 0)

    cost = data.get("cost", {}).get("total_cost_usd", 0) or 0
    duration_ms = data.get("cost", {}).get("total_duration_ms", 0) or 0
    total_in = ctx.get("total_input_tokens", 0) or 0
    total_out = ctx.get("total_output_tokens", 0) or 0
    lines_added = data.get("cost", {}).get("total_lines_added", 0) or 0
    lines_removed = data.get("cost", {}).get("total_lines_removed", 0) or 0

    # Cache hit %
    usage = ctx.get("current_usage", {})
    inp = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0)
    cache_pct = int((usage.get("cache_read_input_tokens") or 0) * 100 / inp) if inp > 0 else 0

    # Color-coded progress bar (earlier thresholds — compaction at 100% is disruptive)
    if pct >= 80:
        bar_color = RED
    elif pct >= 50:
        bar_color = YELLOW
    else:
        bar_color = GREEN

    bar_width = 12
    filled = pct * bar_width // 100
    bar = "\u2588" * filled + f"{DIM}" + "\u28ff" * (bar_width - filled) + f"{RESET}"

    # Duration — adaptive: "45s", "3m 12s", "1h 30m"
    total_sec = duration_ms // 1000
    hours = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        session_time = f"{hours}h {mins}m"
    elif mins > 0:
        session_time = f"{mins}m {secs}s"
    else:
        session_time = f"{secs}s"

    SEP = f" {DIM}│{RESET} "

    # Line 1: [Model] directory | branch
    git = get_git_info()
    line1 = f"\033[37m[{model}]{RESET} \033[94m{directory}{RESET}"
    if git:
        line1 += f"{SEP}\033[96m{git}{RESET}"

    # Format token counts (e.g., 15234 -> 15.2k)
    def fmt_tokens(n):
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}k"
        return str(n)

    # Line 2: progress bar, context %, cost, tokens, duration, lines, cache
    line2 = f"{bar_color}{bar} \033[37m{pct}%{RESET}"
    line2 += f"{SEP}{YELLOW}${cost:.2f}{RESET}"
    line2 += f"{SEP}{DIM}in:{RESET}{fmt_tokens(total_in)} {DIM}out:{RESET}{fmt_tokens(total_out)}"
    line2 += f"{SEP}{CYAN}{session_time}{RESET}"
    if lines_added or lines_removed:
        line2 += f"{SEP}{GREEN}+{lines_added}{RESET}/{RED}-{lines_removed}{RESET}"
    if cache_pct > 0:
        line2 += f" {DIM}\u21bb{cache_pct}%{RESET}"

    print(line1)
    print(line2)


if __name__ == "__main__":
    main()
