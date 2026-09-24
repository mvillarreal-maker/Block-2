#!/usr/bin/env python3
"""Tkinter desktop app for summarizing and classifying student files.

This app reads text files, ignores the first line, asks the AI for a summary,
asks for an independent school_interest guess, and compares that guess to the
Category line in the file.
"""

from __future__ import annotations

import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from openai import OpenAI

API_KEY = "aadf116121ae92286f515d31c7310e60c2ce8cd1c5b76262a96f7211fff50f71"
BASE_URL = "https://ai.valleychristianai.com/v1"
MODEL = "qwen3:latest"
DEFAULT_EXTENSIONS = {".txt", ".md", ".csv", ".rst"}


def read_first_line(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return lines[0].strip() if lines else ""


def read_body_without_first_line(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) <= 1:
        return ""
    return "\n".join(lines[1:]).strip()


def extract_category_from_first_line(line: str) -> str:
    match = re.search(r"Category\s*:\s*(.+)", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "unknown"


def summarize_text(text: str) -> str:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    prompt = (
        "You are summarizing a student's project notes. Ignore the first line if it is a heading or file label. "
        "Read the remaining text and write one short sentence describing what the student is working on. "
        "Keep the summary concise and factual.\n\n"
        f"Student text:\n{text}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def infer_school_interest(text: str) -> str:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    prompt = (
        "Read the student text and choose the most likely school_interest category. "
        "Return only one of these exact labels: Sports, Arts, Science, History, Math, or Other.\n\n"
        f"Student text:\n{text}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = (response.choices[0].message.content or "").strip()
    label = content.strip().split()[0].strip("[](){}.,;:!?")
    return label or "Other"


def analyze_file(path: Path) -> dict:
    first_line = read_first_line(path)
    body = read_body_without_first_line(path)
    category = extract_category_from_first_line(first_line)

    if not body.strip():
        return {
            "name": path.stem,
            "category": category,
            "school_interest": "unknown",
            "matches_category": False,
            "summary": "No content after first line.",
        }

    summary = summarize_text(body)
    school_interest = infer_school_interest(body)
    matches = str(school_interest).lower() == str(category).lower()

    return {
        "name": path.stem,
        "category": category,
        "school_interest": school_interest,
        "matches_category": matches,
        "summary": summary,
    }


def analyze_files(paths):
    results = []
    for path in paths:
        try:
            results.append(analyze_file(Path(path)))
        except Exception as exc:
            results.append({
                "name": Path(path).stem,
                "category": "unknown",
                "school_interest": "unknown",
                "matches_category": False,
                "summary": f"Error: {exc}",
            })
    return results


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lesson 2 AI Student Report")
        self.root.geometry("900x600")
        self.root.minsize(700, 450)

        self.selected_files = []

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Student text files", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        button_row = ttk.Frame(top)
        button_row.pack(fill="x", pady=(8, 0))

        ttk.Button(button_row, text="Select files", command=self.select_files).pack(side="left")
        ttk.Button(button_row, text="Go", command=self.run_analysis).pack(side="left", padx=(10, 0))

        self.file_list_var = tk.StringVar(value="No files selected")
        ttk.Label(top, textvariable=self.file_list_var, wraplength=780, justify="left").pack(anchor="w", pady=(8, 0))

        ttk.Label(root, text="Report", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10)
        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select student files",
            filetypes=[("Text files", "*.txt *.md *.csv *.rst"), ("All files", "*.*")],
        )
        if not paths:
            return
        self.selected_files = list(paths)
        display = "\n".join(Path(p).name for p in self.selected_files)
        self.file_list_var.set(display)
        self.output.insert(tk.END, f"Selected {len(self.selected_files)} files\n")
        self.output.see(tk.END)

    def run_analysis(self):
        if not self.selected_files:
            messagebox.showwarning("No files", "Select one or more student text files first.")
            return

        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "Running analysis...\n")
        self.root.update_idletasks()

        try:
            results = analyze_files(self.selected_files)
        except Exception as exc:
            self.output.insert(tk.END, f"Error: {exc}\n")
            return

        pretty = json.dumps(results, indent=2, ensure_ascii=False)
        self.output.insert(tk.END, pretty)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
