from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk

from ui_agent import run_agent


def _resource_path(relative_path: str) -> str:
    # Resolve bundled resources in both source and PyInstaller contexts.
    base_dir = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_dir, relative_path)


class AISearchAgentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AI Search Agent")
        self.root.geometry("960x720")
        self.root.minsize(780, 560)

        try:
            self.window_icon = tk.PhotoImage(file=_resource_path("assets/app_icon.png"))
            self.root.iconphoto(True, self.window_icon)
        except tk.TclError:
            self.window_icon = None

        self.result_queue: queue.Queue[tuple[str, int, str]] = queue.Queue()
        self.pending_bubbles: dict[int, tk.Frame] = {}
        self.next_request_id = 1
        self.is_busy = False

        self._configure_style()
        self._build_ui()
        self.root.after(100, self._poll_worker_queue)

    def _configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background="#eef3f9")
        style.configure("Header.TFrame", background="#0b2f4a")
        style.configure(
            "Header.TLabel",
            background="#0b2f4a",
            foreground="#f8fbff",
            font=("Segoe UI", 16, "bold"),
            padding=(16, 12),
        )
        style.configure("Input.TFrame", background="#eef3f9")
        style.configure("Send.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 8))

    def _build_ui(self) -> None:
        self.root.configure(background="#eef3f9")
        container = ttk.Frame(self.root, style="Root.TFrame", padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container, style="Header.TFrame")
        header.pack(fill=tk.X)
        ttk.Label(header, text="AI Search Agent", style="Header.TLabel").pack(side=tk.LEFT)

        chat_wrapper = ttk.Frame(container, style="Root.TFrame", padding=(0, 12, 0, 10))
        chat_wrapper.pack(fill=tk.BOTH, expand=True)

        self.chat_canvas = tk.Canvas(
            chat_wrapper,
            background="#eef3f9",
            highlightthickness=0,
            borderwidth=0,
        )
        self.chat_scrollbar = ttk.Scrollbar(
            chat_wrapper,
            orient=tk.VERTICAL,
            command=self.chat_canvas.yview,
        )
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.messages_frame = tk.Frame(self.chat_canvas, background="#eef3f9")
        self.messages_window = self.chat_canvas.create_window(
            (0, 0),
            window=self.messages_frame,
            anchor="nw",
        )

        self.messages_frame.bind("<Configure>", self._on_messages_configure)
        self.chat_canvas.bind("<Configure>", self._on_canvas_configure)

        input_frame = ttk.Frame(container, style="Input.TFrame")
        input_frame.pack(fill=tk.X)

        self.input_box = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=8,
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.input_box.bind("<Return>", self._on_enter_send)
        self.input_box.bind("<Shift-Return>", self._on_shift_enter_newline)

        button_frame = ttk.Frame(input_frame, style="Input.TFrame")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.send_button = ttk.Button(button_frame, text="Send", style="Send.TButton", command=self._send_message)
        self.send_button.pack(fill=tk.X)

        self.clear_button = ttk.Button(button_frame, text="Clear chat", command=self._clear_chat)
        self.clear_button.pack(fill=tk.X, pady=(8, 0))

        self.input_box.focus_set()

    def _on_messages_configure(self, _event: tk.Event) -> None:
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.chat_canvas.itemconfig(self.messages_window, width=event.width)

    def _on_enter_send(self, _event: tk.Event) -> str:
        self._send_message()
        return "break"

    def _on_shift_enter_newline(self, _event: tk.Event) -> str:
        self.input_box.insert(tk.INSERT, "\n")
        return "break"

    def _scroll_to_bottom(self) -> None:
        self.root.after_idle(lambda: self.chat_canvas.yview_moveto(1.0))

    def _create_bubble_row(self, role: str) -> tk.Frame:
        row = tk.Frame(self.messages_frame, background="#eef3f9")
        row.pack(fill=tk.X, pady=6, padx=8)

        if role == "user":
            bubble_bg = "#dbeafe"
            text_fg = "#0f172a"
            pad = (180, 0)
            side = tk.RIGHT
            label_text = "You"
        else:
            bubble_bg = "#ffffff"
            text_fg = "#0f172a"
            pad = (0, 180)
            side = tk.LEFT
            label_text = "Assistant"

        bubble = tk.Frame(
            row,
            background=bubble_bg,
            highlightbackground="#cbd5e1",
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        bubble.pack(side=side, padx=pad)

        header = tk.Label(
            bubble,
            text=label_text,
            bg=bubble_bg,
            fg="#334155",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        header.pack(fill=tk.X)

        content = tk.Frame(bubble, background=bubble_bg)
        content.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        if role == "user":
            content.text_fg = text_fg  # type: ignore[attr-defined]
            content.bg = bubble_bg  # type: ignore[attr-defined]
        else:
            content.text_fg = text_fg  # type: ignore[attr-defined]
            content.bg = bubble_bg  # type: ignore[attr-defined]

        return content

    def _render_plain_text(self, container: tk.Frame, text: str, *, italic: bool = False, error: bool = False) -> None:
        for child in container.winfo_children():
            child.destroy()

        font = ("Segoe UI", 11, "italic") if italic else ("Segoe UI", 11)
        fg = "#b42318" if error else getattr(container, "text_fg", "#0f172a")
        label = tk.Label(
            container,
            text=text,
            justify=tk.LEFT,
            anchor="w",
            wraplength=620,
            bg=getattr(container, "bg", "#ffffff"),
            fg=fg,
            font=font,
        )
        label.pack(fill=tk.X)

    def _append_user_message(self, message: str) -> None:
        content = self._create_bubble_row("user")
        self._render_plain_text(content, message)
        self._scroll_to_bottom()

    def _append_thinking_bubble(self, request_id: int) -> None:
        content = self._create_bubble_row("assistant")
        self._render_plain_text(content, "Thinking...", italic=True)
        self.pending_bubbles[request_id] = content
        self._scroll_to_bottom()

    def _replace_thinking_with_success(self, request_id: int, answer: str) -> None:
        container = self.pending_bubbles.pop(request_id, None)
        if container is None:
            return
        self._render_plain_text(container, answer)
        self._scroll_to_bottom()

    def _replace_thinking_with_error(self, request_id: int, message: str) -> None:
        container = self.pending_bubbles.pop(request_id, None)
        if container is None:
            return
        self._render_plain_text(container, message, error=True)
        self._scroll_to_bottom()

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.input_box.configure(state=state)
        self.send_button.configure(state=state)
        if not busy:
            self.input_box.focus_set()

    def _clear_chat(self) -> None:
        for child in self.messages_frame.winfo_children():
            child.destroy()
        self.pending_bubbles.clear()

    def _worker_search(self, request_id: int, query: str) -> None:
        try:
            answer = run_agent(query)
            self.result_queue.put(("ok", request_id, answer))
        except Exception as error:  # pragma: no cover - GUI path
            self.result_queue.put(("error", request_id, str(error)))

    def _send_message(self) -> None:
        if self.is_busy:
            return

        query = self.input_box.get("1.0", tk.END).strip()
        if not query:
            return

        request_id = self.next_request_id
        self.next_request_id += 1

        self._append_user_message(query)
        self.input_box.delete("1.0", tk.END)
        self._append_thinking_bubble(request_id)
        self._set_busy(True)

        worker = threading.Thread(target=self._worker_search, args=(request_id, query), daemon=True)
        worker.start()

    def _poll_worker_queue(self) -> None:
        try:
            while True:
                status, request_id, payload = self.result_queue.get_nowait()
                if status == "ok":
                    self._replace_thinking_with_success(request_id, payload)
                else:
                    self._replace_thinking_with_error(
                        request_id,
                        payload or "Sorry, something went wrong while searching. Please try again.",
                    )
                self._set_busy(False)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_worker_queue)


def launch_gui() -> int:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Unable to start the desktop window: {error}")
        return 1

    AISearchAgentApp(root)
    root.mainloop()
    return 0
