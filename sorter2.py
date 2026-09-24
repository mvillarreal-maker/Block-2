#!/usr/bin/env python3
"""Summarize student work from text files using the VCS OpenAI-compatible API.

This script intentionally ignores the first line in every file and summarizes the
remaining content in a single sentence using the provided model and base URL.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from openai import OpenAI

API_KEY = "aadf116121ae92286f515d31c7310e60c2ce8cd1c5b76262a96f7211fff50f71"
BASE_URL = "https://ai.valleychristianai.com/v1"
MODEL = "qwen3:latest"

DEFAULT_EXTENSIONS = {".txt", ".md", ".csv", ".rst"}
SKIP_DIRS = {".git", "node_modules", ".next", "__pycache__", ".venv"}


def iter_files(root: Path) -> Iterable[Path]:
    """Yield candidate text files under the target directory, skipping large/generated folders."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in DEFAULT_EXTENSIONS:
            yield path


def read_first_line(path: Path) -> str:
    """Read the first line of the file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        return ""
    return lines[0].strip()


def read_body_without_first_line(path: Path) -> str:
    """Return the contents of the file after its first line."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) <= 1:
        return ""
    return "\n".join(lines[1:]).strip()


def summarize_text(text: str) -> str:
    """Summarize the given text in a single sentence using the configured model."""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    prompt = (
        "You are summarizing a student's project notes. Ignore the first line if it is a heading or file label. "
        "Read the remaining text and write one short sentence describing what the student is working on. "
        "Keep the summary concise and factual.\n\n"
        f"Student text:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI request failed for model '{MODEL}' at '{BASE_URL}': {exc}"
        ) from exc

    content = response.choices[0].message.content
    return (content or "").strip()


def infer_school_interest(text: str) -> str:
    """Use the model to infer the student's likely school_interest category."""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    prompt = (
        "Read the student text and decide the most likely school_interest category. "
        "Return only one of these exact labels: AI, AR, Robotics, Data, Programming, Design, or Other.\n\n"
        f"Student text:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI request failed for model '{MODEL}' at '{BASE_URL}': {exc}"
        ) from exc

    content = (response.choices[0].message.content or "").strip()
    label = content.strip().split()[0].strip("[](){}.,;:!?")
    return label or "Other"


def extract_name_from_file_name(path: Path) -> str:
    """Best-effort extraction of a person's name from the file name."""
    name = path.stem.replace("_", " ").replace("-", " ").strip()
    return name or "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize student work from text files.")
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(Path.cwd()),
        help="Directory containing student files to summarize (defaults to current folder).",
    )
    args = parser.parse_args()

    root = Path(args.directory).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Directory does not exist: {root}")

    files = list(iter_files(root))
    if not files:
        raise SystemExit("[]")

    report = []
    for file_path in files:
        first_line = read_first_line(file_path)
        body = read_body_without_first_line(file_path)
        if not body.strip():
            continue

        category_match = re.search(r"Category\s*:\s*(.+)", first_line, flags=re.IGNORECASE)
        category = category_match.group(1).strip() if category_match else "unknown"

        try:
            summary = summarize_text(body)
            school_interest = infer_school_interest(body)
        except Exception:
            continue

        matches = str(school_interest).lower() == str(category).lower()
        report.append({
            "name": extract_name_from_file_name(file_path),
            "category": category,
            "school_interest": school_interest,
            "matches_category": matches,
            "summary": summary,
        })

    if not report:
        raise SystemExit("[]")

    print(report)


if __name__ == "__main__":
    main()
