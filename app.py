import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import PDF_QA  # our helper module

class QA:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Chatbot")
        self.window.geometry("600x780")

        # state
        self.file_path = ""
        self.history = []            # list[(user, bot)]
        self.chain = None            # set after upload

        # UI
        self.chat_log = ScrolledText(self.window, wrap=tk.WORD, state=tk.DISABLED)
        self.user_input = ttk.Entry(self.window)
        self.send_button = ttk.Button(self.window, text="Ask", command=self.on_send_clicked)
        self.upload_button = ttk.Button(self.window, text="Upload PDF", command=self.upload_file)

        self.chat_log.pack(padx=10, pady=(10, 6), fill=tk.BOTH, expand=True)
        self.user_input.pack(padx=10, pady=6, fill=tk.X)
        self.send_button.pack(padx=10, pady=6)
        self.upload_button.pack(padx=10, pady=(0, 10))

        # bindings
        self.user_input.bind("<Return>", lambda e: self.on_send_clicked())

        # tags for colors
        self._init_tags()

    # --- UI helpers
    def _init_tags(self):
        self.chat_log.configure(font=("Segoe UI", 10))
        self._add_tag("user_prefix", "blue")
        self._add_tag("bot_prefix", "purple")
        self._add_tag("sys_prefix", "gray25")
        self._add_tag("user_text", "black")
        self._add_tag("bot_text", "black")
        self._add_tag("sys_text", "gray40")

    def _add_tag(self, name, fg):
        self.chat_log.tag_configure(name, foreground=fg)

    def _append_rich(self, prefix, prefix_tag, text, text_tag):
        self.chat_log.configure(state=tk.NORMAL)
        self.chat_log.insert(tk.END, prefix, prefix_tag)
        self.chat_log.insert(tk.END, text + "\n", text_tag)
        self.chat_log.configure(state=tk.DISABLED)
        self.chat_log.see(tk.END)

    def _append_user(self, text):
        self._append_rich("You: ", "user_prefix", text, "user_text")

    def _append_bot(self, text):
        self._append_rich("Bot: ", "bot_prefix", text, "bot_text")

    def _append_sys(self, text):
        self._append_rich("Info: ", "sys_prefix", text, "sys_text")

    # --- events
    def on_send_clicked(self):
        query = self.user_input.get().strip()
        if not query:
            return
        self._append_user(query)
        self.user_input.delete(0, tk.END)

        if not self.chain:
            self._append_bot("Please upload a PDF document first.")
            return

        # run in a thread to prevent UI freeze
        threading.Thread(target=self._ask_thread, args=(query,), daemon=True).start()

    def _ask_thread(self, query):
        try:
            result = self.chain({"question": query, "chat_history": self.history})
            answer = result.get("answer", "").strip() or "(no answer)"
        except Exception as e:
            answer = f"Error: {e}"
        self.history.append((query, answer))
        self.window.after(0, lambda: self._append_bot(answer))

    def upload_file(self):
        path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not path:
            return

        self.file_path = path
        self._append_sys(f"Loaded file: {os.path.basename(path)}")
        self._append_sys("Building index… (this happens once per file)")

        def build_chain():
            try:
                self.chain = PDF_QA.get_chain(self.file_path)
                msg = "Ready! Ask a question about the document."
            except Exception as e:
                self.chain = None
                msg = f"Failed to build index: {e}"
            self.window.after(0, lambda: self._append_sys(msg))

        threading.Thread(target=build_chain, daemon=True).start()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    # Ensure the API key is set from your environment (recommended)
    if not os.environ.get("OPENAI_API_KEY"):
        messagebox.showwarning(
            "OpenAI API Key",
            "Set the OPENAI_API_KEY environment variable before running."
        )
    QA().run()
