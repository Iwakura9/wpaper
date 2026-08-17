<div align="center">

# WPAPER

</div>

**wpaper is a terminal-based notes and personal organization app built to make writing, tracking tasks, and accessing important information fast without leaving the command line.**

## Idea

wpaper was created from the idea of having a simple and focused workspace inside the terminal.

Instead of depending on heavy note-taking apps, browser tabs, or complex productivity systems, wpaper aims to provide a lightweight TUI for quickly creating notes, managing tasks, and checking useful information from one place.
The goal is to feel closer to tools like Neovim, being fast, keyboard-driven, minimal, and comfy.

## Features

* Create, write and manage notes
* Register and organize tasks (importance, deadline, status)
* Link notes to tasks
* Tags with autocomplete suggestions
* Dashboard with stats, open tasks and a note board (grid/kanban)
* Keyboard-driven navigation
* Lightweight TUI interface

## How to install

```bash
git clone https://github.com/Iwakura9/wpaper.git
cd wpaper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to run

```bash
source .venv/bin/activate
python wpaper.py
```
