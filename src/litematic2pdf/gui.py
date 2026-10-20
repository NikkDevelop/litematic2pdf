"""Tkinter GUI: pick a .litematic, enter guide title/description, create the PDF.

Runs the exact same pipeline as the CLI (litematic2pdf.cli.main) in a worker
thread; stdout is streamed into the built-in log.
"""
import os
import queue
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import BRAND, __version__

BG = "#f2ead8"
CARD = "#faf5e9"
ACCENT = "#6b4f3a"
TEXT = "#4a3a3a"
MUTED = "#8a7a66"


class _QueueStdout:
    """Minimal file-like that pushes written text into a queue."""

    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(("log", text))

    def flush(self):
        pass


class GuideApp:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.worker = None
        self.last_pdf = None
        root.title(f"Litematica → 2D Build Guide · v{__version__}")
        root.configure(bg=BG)
        root.geometry("600x640")
        root.minsize(560, 600)
        self._build_widgets()
        root.after(120, self._poll_log)

    # ---------- UI ----------
    def _label(self, parent, text, row, col=0):
        tk.Label(parent, text=text, bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).grid(row=row, column=col,
                                             sticky="w", pady=(8, 1))

    def _build_widgets(self):
        pad = dict(padx=14)
        head = tk.Frame(self.root, bg=BG)
        head.pack(fill="x", **pad)
        tk.Label(head, text="2D Build Guide Maker", bg=BG, fg=ACCENT,
                 font=("Segoe UI Semibold", 17)).pack(anchor="w", pady=(12, 0))
        tk.Label(head, text=f"схема .litematic → продажный PDF-гайд · {BRAND}",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, **pad)
        body.columnconfigure(1, weight=1)

        # schematic file
        self._label(body, "Схема .litematic", 0)
        self.src_var = tk.StringVar()
        ttk.Entry(body, textvariable=self.src_var).grid(
            row=1, column=0, columnspan=2, sticky="ew")
        tk.Button(body, text="Обзор…", command=self._pick_file, bd=0,
                  bg=ACCENT, fg="white", activebackground="#5a4030",
                  activeforeground="white", padx=10, pady=2,
                  cursor="hand2").grid(row=1, column=2, padx=(6, 0))

        # guide name
        self._label(body, "Название гайда (будет на обложке)", 2)
        self.name_var = tk.StringVar()
        ttk.Entry(body, textvariable=self.name_var).grid(
            row=3, column=0, columnspan=3, sticky="ew")

        # description
        self._label(body, "Описание для обложки (необязательно)", 4)
        self.desc = tk.Text(body, height=3, wrap="word", bg=CARD, fg=TEXT,
                            relief="flat", font=("Segoe UI", 10),
                            insertbackground=TEXT, padx=6, pady=4)
        self.desc.grid(row=5, column=0, columnspan=3, sticky="ew", ipady=2)

        # region + axis
        self._label(body, "Регион схемы", 6)
        self._label(body, "Разрезать по оси", 6, col=1)
        self.region_var = tk.StringVar(value="все регионы")
        self.region_box = ttk.Combobox(body, textvariable=self.region_var,
                                       values=["все регионы"], state="readonly",
                                       width=24)
        self.region_box.grid(row=7, column=0, columnspan=2, sticky="w")
        self.axis_var = tk.StringVar(value="y")
        axes = tk.Frame(body, bg=BG)
        axes.grid(row=7, column=2, sticky="e")
        for text, val in (("слои Y", "y"), ("фасад Z", "z"), ("профиль X", "x")):
            tk.Radiobutton(axes, text=text, value=val, variable=self.axis_var,
                           bg=BG, fg=TEXT, selectcolor=CARD, bd=0,
                           highlightthickness=0).pack(side="left")

        # brand / watermark
        self._label(body, "Водяной знак (бренд на страницах)", 8)
        brow = tk.Frame(body, bg=BG)
        brow.grid(row=9, column=0, columnspan=3, sticky="ew")
        self.brand_var = tk.StringVar(value=BRAND)
        ttk.Entry(brow, textvariable=self.brand_var, width=30).pack(side="left")
        self.show_wm = tk.BooleanVar(value=True)
        tk.Checkbutton(brow, text="показывать", variable=self.show_wm, bg=BG,
                       fg=MUTED, selectcolor=CARD, bd=0,
                       highlightthickness=0).pack(side="left", padx=10)

        # output
        self._label(body, "Сохранить PDF (пусто = рядом со схемой)", 10)
        self.out_var = tk.StringVar()
        ttk.Entry(body, textvariable=self.out_var).grid(
            row=11, column=0, columnspan=2, sticky="ew")
        tk.Button(body, text="Обзор…", command=self._pick_out, bd=0,
                  bg=ACCENT, fg="white", activebackground="#5a4030",
                  activeforeground="white", padx=10, pady=2,
                  cursor="hand2").grid(row=11, column=2, padx=(6, 0))

        # go
        action = tk.Frame(body, bg=BG)
        action.grid(row=12, column=0, columnspan=3, sticky="ew", pady=12)
        self.go_btn = tk.Button(action, text="СОЗДАТЬ PDF", command=self._start,
                                bd=0, bg=ACCENT, fg="white",
                                activebackground="#5a4030", activeforeground="white",
                                font=("Segoe UI Semibold", 11, "bold"),
                                padx=22, pady=8, cursor="hand2")
        self.go_btn.pack(side="left")
        self.open_btn = tk.Button(action, text="Открыть PDF", command=self._open_pdf,
                                  state="disabled", bd=0, bg="#d9cbaa", fg=MUTED,
                                  font=("Segoe UI", 10), padx=14, pady=8,
                                  cursor="hand2")
        self.open_btn.pack(side="left", padx=8)
        self.progress = ttk.Progressbar(action, mode="indeterminate", length=150)
        self.progress.pack(side="right")

        # log
        self.log = tk.Text(body, height=8, bg=CARD, fg=MUTED, relief="flat",
                           font=("Consolas", 9), state="disabled", wrap="word",
                           padx=6, pady=4)
        self.log.grid(row=13, column=0, columnspan=3, sticky="nsew")
        body.rowconfigure(13, weight=1)

    # ---------- callbacks ----------
    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Выберите .litematic",
            filetypes=[("Litematica schematics", "*.litematic"), ("All files", "*.*")])
        if not path:
            return
        self.src_var.set(path)
        stem = Path(path).stem.replace("_", " ").replace("-", " ")
        if not self.name_var.get().strip():
            self.name_var.set(stem.title())
        self._load_regions(path)

    def _pick_out(self):
        src = self.src_var.get().strip()
        types = [("PDF", "*.pdf")]
        pdf = filedialog.asksaveasfilename(title="Куда сохранить PDF",
                                           defaultextension=".pdf", filetypes=types,
                                           initialdir=str(Path(src).parent) if src else "")
        if pdf:
            self.out_var.set(pdf)

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _load_regions(self, path):
        def job():
            try:
                from .schema import load_litematic
                root = load_litematic(Path(path))
                names = ["все регионы"] + list(root.get("Regions", {}).keys())
                self.q.put(("regions", names))
            except Exception as e:
                self.q.put(("log", f"! регионы не прочитались: {e}\n"))
        threading.Thread(target=job, daemon=True).start()

    def _start(self):
        if self.worker and self.worker.is_alive():
            return
        src = self.src_var.get().strip()
        if not src:
            messagebox.showwarning("Файл не выбран", "Сначала выберите .litematic")
            return
        if not Path(src).exists():
            messagebox.showerror("Ошибка", "Файл схемы не найден")
            return
        if not self.name_var.get().strip():
            self.name_var.set(Path(src).stem.title())
        out = self.out_var.get().strip() or str(Path(src).with_suffix(".pdf"))
        argv = [src, "-o", out,
                "--title", self.name_var.get().strip(),
                "--description", self.desc.get("1.0", "end").strip(),
                "--axis", self.axis_var.get()]
        region = self.region_var.get()
        if region and region != "все регионы":
            argv += ["--regions", region]
        if self.show_wm.get():
            argv += ["--watermark", self.brand_var.get().strip() or BRAND]
        else:
            argv += ["--no-watermark"]
        self.last_pdf = out
        self.go_btn.configure(state="disabled")
        self.open_btn.configure(state="disabled", bg="#d9cbaa", fg=MUTED)
        self.progress.start(12)
        self._log(f"→ запуск: {Path(src).name}\n")

        def job():
            real_stdout = sys.stdout
            sys.stdout = _QueueStdout(self.q)
            code = 0
            try:
                from .cli import main
                main(argv)
            except SystemExit as e:  # cli exits via sys.exit on errors
                code = e.code if isinstance(e.code, int) else 1
                if e.code and not isinstance(e.code, int):
                    self.q.put(("log", f"Ошибка: {e.code}\n"))
            except BaseException as e:
                code = 1
                self.q.put(("log", f"Ошибка: {type(e).__name__}: {e}\n"))
            finally:
                sys.stdout = real_stdout
                self.q.put(("done", code))
        self.worker = threading.Thread(target=job, daemon=True)
        self.worker.start()

    def _poll_log(self):
        try:
            while True:
                try:
                    item = self.q.get_nowait()
                except queue.Empty:
                    break
                if isinstance(item, tuple) and len(item) == 2:
                    kind, payload = item
                else:  # anything unexpected -> just a log line, never crash
                    kind, payload = "log", str(item)
                if kind == "log":
                    self._log(payload)
                elif kind == "regions":
                    self.region_box.configure(values=payload)
                    self.region_box.current(0)
                elif kind == "done":
                    self.progress.stop()
                    self.go_btn.configure(state="normal")
                    if payload == 0 and self.last_pdf and Path(self.last_pdf).exists():
                        self.open_btn.configure(state="normal", bg=ACCENT, fg="white")
                        kb = Path(self.last_pdf).stat().st_size // 1024
                        self._log(f"✔ PDF готов: {self.last_pdf} ({kb} КБ)\n")
                        messagebox.showinfo("Готово",
                                            f"PDF создан ({kb} КБ).\n"
                                            f"{self.last_pdf}")
                    else:
                        messagebox.showerror("Не получилось",
                                             "Смотрите лог в окне программы.")
        finally:
            # the poller must survive any handler error, otherwise the
            # progress bar keeps spinning forever
            self.root.after(120, self._poll_log)

    def _open_pdf(self):
        if self.last_pdf and Path(self.last_pdf).exists():
            try:
                os.startfile(self.last_pdf)  # Windows
            except OSError:
                pass


def _selftest():
    """Headless full-pipeline run inside the exe (no window): builds a test
    PDF from the bundled sample schematic and reports via a temp file."""
    import tempfile
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    src = base / "Villager-House-Sake.litematic"
    out_dir = Path(tempfile.gettempdir()) / "opencode"
    out_dir.mkdir(exist_ok=True)
    result = out_dir / "selftest_ok.txt"
    for stale in (result, out_dir / "selftest.pdf"):
        if stale.exists():
            stale.unlink()
    try:
        from .cli import main as cli_main
        cli_main([str(src), "-o", str(out_dir / "selftest.pdf"),
                  "--title", "Selftest"])
        ok = (out_dir / "selftest.pdf").exists()
        result.write_text("ok" if ok else "no-pdf", encoding="utf-8")
        return 0 if ok else 1
    except SystemExit as e:
        result.write_text(f"exit {e.code}", encoding="utf-8")
        return 1
    except BaseException:
        import traceback
        result.write_text(traceback.format_exc(), encoding="utf-8")
        return 1


def main():
    if "--selftest" in sys.argv:
        return _selftest()
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        style.theme_use("clam")
    except tk.TclError:
        pass
    GuideApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
