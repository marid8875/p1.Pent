#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pentest Suite - a single GUI that wraps common Linux pentesting tools.

The user never types a command: pick a tool from the list, fill in the
target (and wordlist, if the tool needs one), and click Run. Output streams
live into the console panel below.
"""

import os
import sys
import shutil
import shlex
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QTextEdit, QLabel, QFileDialog, QMessageBox, QSplitter, QGroupBox,
    QFormLayout
)
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont, QTextCursor

from tools_config import TOOLS

APP_TITLE = "Pentest Suite — Unified Pentesting Toolkit"

# Terminal emulators to try, in order, for tools that must run interactively
# in their own window (see "external_terminal" in tools_config.py).
TERMINAL_CANDIDATES = [
    ("x-terminal-emulator", ["-e"]),
    ("gnome-terminal", ["--"]),
    ("konsole", ["-e"]),
    ("xfce4-terminal", ["-e"]),
    ("xterm", ["-e"]),
]


class PentestSuite(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(950, 650)

        self.process = None
        self.current_tool = None

        self._build_ui()

    # ---------------------------------------------------------------- UI --
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---- Target / wordlist input ----
        input_box = QGroupBox("Target Settings")
        form = QFormLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(
            "e.g. 192.168.1.10, example.com, or http://example.com"
        )
        form.addRow("Target (IP / Domain / URL):", self.target_input)

        wl_row = QHBoxLayout()
        self.wordlist_input = QLineEdit()
        self.wordlist_input.setPlaceholderText(
            "Only needed by some tools (password cracking, Gobuster, "
            "a port number for Netcat...)"
        )
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_wordlist)
        wl_row.addWidget(self.wordlist_input)
        wl_row.addWidget(browse_btn)
        form.addRow("Wordlist / Extra Value:", wl_row)

        input_box.setLayout(form)
        main_layout.addWidget(input_box)

        # ---- Tool tabs + details ----
        splitter = QSplitter(Qt.Vertical)

        self.tabs = QTabWidget()
        self.category_lists = {}
        for category, tools in TOOLS.items():
            lst = QListWidget()
            for tool in tools:
                item = QListWidgetItem(tool["name"])
                item.setData(Qt.UserRole, tool)
                lst.addItem(item)
            lst.itemClicked.connect(self._on_tool_selected)
            lst.itemDoubleClicked.connect(self._on_run_clicked)
            self.category_lists[category] = lst
            self.tabs.addTab(lst, category)

        splitter.addWidget(self.tabs)

        desc_box = QGroupBox("Selected Tool Details")
        desc_layout = QVBoxLayout()
        self.desc_label = QLabel("Select a tool above to see its description.")
        self.desc_label.setWordWrap(True)
        self.cmd_preview = QLineEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setStyleSheet("background:#f0f0f0; font-family: monospace;")
        desc_layout.addWidget(self.desc_label)
        desc_layout.addWidget(QLabel("Command that will actually run:"))
        desc_layout.addWidget(self.cmd_preview)
        desc_box.setLayout(desc_layout)
        splitter.addWidget(desc_box)

        splitter.setSizes([350, 100])
        main_layout.addWidget(splitter)

        # ---- Controls ----
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setStyleSheet(
            "background:#2e7d32; color:white; font-weight:bold; padding:8px;"
        )
        self.run_btn.clicked.connect(self._on_run_clicked)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setStyleSheet(
            "background:#c62828; color:white; font-weight:bold; padding:8px;"
        )
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)

        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(lambda: self.output.clear())

        self.save_btn = QPushButton("Save Output...")
        self.save_btn.clicked.connect(self._save_output)

        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.save_btn)
        main_layout.addLayout(btn_row)

        # ---- Output console ----
        main_layout.addWidget(QLabel("Live Output:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Monospace", 10))
        self.output.setStyleSheet("background:#0d0d0d; color:#00ff66;")
        main_layout.addWidget(self.output, stretch=1)

        self.status_label = QLabel("Ready.")
        main_layout.addWidget(self.status_label)

    # ---------------------------------------------------------- helpers --
    def _browse_wordlist(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist File")
        if path:
            self.wordlist_input.setText(path)

    def _on_tool_selected(self, item: QListWidgetItem):
        tool = item.data(Qt.UserRole)
        self.current_tool = tool
        self.desc_label.setText(f"<b>{tool['name']}</b><br>{tool['desc']}")
        self.cmd_preview.setText(self._build_command(tool, preview=True))

    def _build_command(self, tool, preview=False):
        """Build the final command string.

        In preview mode, raw (unquoted) placeholder text is shown so the
        user can read it easily. For actual execution, values are shell-quoted
        with shlex.quote to avoid breaking on spaces/special characters.
        """
        raw_target = self.target_input.text().strip() or "<target>"
        raw_wordlist = self.wordlist_input.text().strip() or "<wordlist/value>"

        if preview:
            target, wordlist = raw_target, raw_wordlist
        else:
            target = shlex.quote(raw_target)
            wordlist = shlex.quote(raw_wordlist)

        try:
            return tool["cmd"].format(target=target, wordlist=wordlist)
        except Exception:
            return tool["cmd"]

    def _tool_binary_missing(self, cmd_str):
        """Check whether the tool's underlying binary is installed."""
        try:
            binary = shlex.split(cmd_str)[0]
        except Exception:
            binary = cmd_str.split()[0]
        return shutil.which(binary) is None

    def _find_terminal_emulator(self):
        for binary, args in TERMINAL_CANDIDATES:
            if shutil.which(binary):
                return binary, args
        return None, None

    # ------------------------------------------------------- pre-checks --
    def _run_preflight_checks(self, tool):
        """Returns True if it's safe to proceed, False to abort (with a
        message already shown to the user)."""

        if tool.get("requires_wordlist") and not self.wordlist_input.text().strip():
            QMessageBox.warning(
                self, "Missing Value",
                "This tool requires a value in the 'Wordlist / Extra Value' "
                "field (a wordlist file path, a hash file, or a port number "
                "depending on the tool)."
            )
            return False

        wl = self.wordlist_input.text().strip()
        if tool.get("requires_wordlist") and wl and not os.path.exists(wl):
            # Only validate as a path for tools whose wordlist field really
            # is a filesystem path (not e.g. a bare port number for Netcat).
            if "{wordlist}" in tool["cmd"] and "nc -l" not in tool["cmd"]:
                confirm = QMessageBox.question(
                    self, "File Not Found",
                    f"The path '{wl}' does not exist on disk. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm != QMessageBox.Yes:
                    return False

        if tool.get("requires_root") and hasattr(os, "geteuid") and os.geteuid() != 0:
            confirm = QMessageBox.question(
                self, "Root Privileges Likely Required",
                "This tool usually needs to run as root (sudo). You are not "
                "running this app as root, so it will probably fail with a "
                "permissions error. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return False

        return True

    # ------------------------------------------------------------- run --
    def _on_run_clicked(self):
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(
                self, "Busy",
                "A command is already running. Wait for it to finish or click Stop."
            )
            return

        if self.current_tool is None:
            QMessageBox.warning(self, "No Tool Selected", "Please select a tool from the list first.")
            return

        if not self.target_input.text().strip():
            QMessageBox.warning(self, "No Target", "Please enter a target first.")
            return

        tool = self.current_tool

        if not self._run_preflight_checks(tool):
            return

        cmd_str = self._build_command(tool)

        if self._tool_binary_missing(cmd_str):
            binary = shlex.split(cmd_str)[0]
            QMessageBox.critical(
                self, "Tool Not Installed",
                f"The program '{binary}' was not found on this system.\n"
                f"Install it first (it is usually preinstalled on Kali Linux, "
                f"or available via apt)."
            )
            return

        confirm = QMessageBox.question(
            self, "Confirm Execution",
            "Make sure you are legally authorized to test this target.\n\n"
            f"The following command will run:\n{cmd_str}\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        if tool.get("external_terminal"):
            self._run_in_external_terminal(cmd_str, tool)
            return

        self.output.append(
            f"\n{'=' * 60}\n[{datetime.now().strftime('%H:%M:%S')}] "
            f"Running: {cmd_str}\n{'=' * 60}\n"
        )
        self.status_label.setText(f"Running: {tool['name']} ...")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

        parts = shlex.split(cmd_str)
        self.process.start(parts[0], parts[1:])

    def _run_in_external_terminal(self, cmd_str, tool):
        binary, args = self._find_terminal_emulator()
        if not binary:
            QMessageBox.critical(
                self, "No Terminal Emulator Found",
                "This tool must run in its own interactive terminal window, "
                "but no terminal emulator (x-terminal-emulator, gnome-terminal, "
                "konsole, xfce4-terminal, xterm) was found on this system.\n\n"
                f"Run it manually instead:\n{cmd_str}"
            )
            return
        try:
            import subprocess
            subprocess.Popen([binary, *args, "bash", "-c", f"{cmd_str}; exec bash"])
            self.output.append(
                f"\n[{tool['name']}] launched in an external terminal window "
                f"({binary}).\n"
            )
            self.status_label.setText(f"{tool['name']} launched in external terminal.")
        except Exception as e:
            QMessageBox.critical(self, "Launch Failed", f"Could not open a terminal: {e}")

    def _on_stop_clicked(self):
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.output.append("\n[Execution stopped by user]\n")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped.")

    def _read_output(self):
        data = self.process.readAllStandardOutput().data().decode(errors="replace")
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(data)
        self.output.moveCursor(QTextCursor.End)

    def _on_finished(self, exit_code, exit_status):
        self.output.append(f"\n[Finished - exit code: {exit_code}]\n")
        self.status_label.setText("Ready.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_error(self, error):
        self.output.append(f"\n[Process error: {error}]\n")
        self.status_label.setText("Error.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _save_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Output", "pentest_output.txt")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.output.toPlainText())
                QMessageBox.information(self, "Saved", f"Output saved to:\n{path}")
            except OSError as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save file: {e}")


def main():
    app = QApplication(sys.argv)
    win = PentestSuite()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
