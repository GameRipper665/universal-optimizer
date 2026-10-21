"""universal-optimizer: make PC games you own run faster, and prove it with numbers.

    uo plan "<game>"                       # engine, graphics API, 32-bit/LAA, upscalers, layers, anti-cheat -> playbook
    uo bench <pid|exe> -o before.json      # frame times (PresentMon), CPU, busiest thread, memory
    uo compare before.json after.json      # what actually changed
    uo proc <pid> --priority high --affinity 0-7

Start with skills/optimize-any-game/SKILL.md.
"""

__version__ = "0.1.0"
