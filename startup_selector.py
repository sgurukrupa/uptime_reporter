"""
Pick which of today's startup/wake events uptime_reporter should count from.

Lists the same System-log events that uptime_reporter treats as startups and
writes the chosen one to uptime_lock.json (overwriting any existing lock).
A uptime_reporter that is already running keeps the start time it loaded, so
restart it after choosing.

Usage:
    python startup_selector.py

Dependencies: pip install pywin32 (plus those of uptime_reporter.py)
"""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from uptime_reporter import (
    get_todays_boot_events,
    load_locked_boot_time,
    save_locked_boot_time,
)


def _plain(dt: datetime.datetime) -> datetime.datetime:
    """Convert pywin32's datetime subclass to a plain naive datetime."""
    return datetime.datetime(*dt.timetuple()[:6])


class StartupSelector:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.events: list[tuple[datetime.datetime, str]] = []
        root.title("Choose uptime start event")
        root.minsize(380, 300)

        self._header = ttk.Label(root, font=("Segoe UI", 10, "bold"))
        self._header.pack(anchor="w", padx=10, pady=(10, 0))
        self._lock_lbl = ttk.Label(root)
        self._lock_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True, padx=10)
        self._tree = ttk.Treeview(
            frame, columns=("time", "kind", "locked"), show="headings",
            selectmode="browse", height=10,
        )
        self._tree.heading("time", text="Time")
        self._tree.heading("kind", text="Event")
        self._tree.heading("locked", text="")
        self._tree.column("time", width=90, anchor="w")
        self._tree.column("kind", width=190, anchor="w")
        self._tree.column("locked", width=70, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._tree.bind("<Double-1>", lambda _e: self._choose())
        self._tree.bind("<Return>", lambda _e: self._choose())

        self._status = ttk.Label(root, foreground="#475569", wraplength=360, justify="left")
        self._status.pack(anchor="w", padx=10, pady=6)

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Set as start time", command=self._choose).pack(side="left")
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=root.destroy).pack(side="right")

        self.refresh()

    def refresh(self):
        today = datetime.date.today()
        self._header.config(text=f"Startup events on {today:%A, %d %b %Y}")
        try:
            self.events = [(_plain(dt), kind) for dt, kind in get_todays_boot_events()]
        except Exception as exc:  # event log access can fail (permissions, pywin32)
            self.events = []
            messagebox.showerror("Could not read event log", str(exc), parent=self.root)

        locked = load_locked_boot_time()
        self._lock_lbl.config(
            text=f"Currently locked: {locked:%H:%M:%S}" if locked else "Currently locked: none"
        )

        self._tree.delete(*self._tree.get_children())
        for i, (dt, kind) in enumerate(self.events):
            mark = "\u2714 locked" if locked == dt else ""
            self._tree.insert("", "end", iid=str(i), values=(dt.strftime("%H:%M:%S"), kind, mark))
        if self.events:
            self._tree.selection_set("0")
            self._status.config(text="Select an event and click \u201cSet as start time\u201d.")
        else:
            self._status.config(text="No startup events found for today.")

    def _choose(self):
        sel = self._tree.selection()
        if not sel:
            return
        dt, kind = self.events[int(sel[0])]
        save_locked_boot_time(dt)
        if load_locked_boot_time() != dt:
            messagebox.showerror(
                "Not saved", "Could not write uptime_lock.json.", parent=self.root
            )
            return
        self.refresh()
        self._status.config(
            text=f"Locked {dt:%H:%M:%S} ({kind}). A running uptime_reporter keeps its old "
                 "start time until it is restarted."
        )


def main():
    root = tk.Tk()
    StartupSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
