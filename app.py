"""Application entry point for the local voice assistant."""

import tkinter as tk

from ui import App


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
