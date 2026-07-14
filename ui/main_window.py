from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QLabel, QMessageBox, QAction,
                             QFrame, QScrollArea, QToolBar, QSizePolicy,
                             QLineEdit, QPushButton, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QFont
import os
import re

from .terminal_widget import TerminalWidget
from .panel_widget import UniversalPanel
from .themes import DARK_THEME, LIGHT_THEME
from . import theme_state
from core.simh_controller import SIMHController
from core.config_loader import ConfigLoader

APP_VERSION = "3.2"

# Typical SIMH interactive-console reply to EXAMINE/DEPOSIT looks like
# "1000:  012345" (radix depends on the machine, usually octal/hex/decimal).
_RE_ADDR_VAL = re.compile(r'^\s*([0-9A-Za-z]+):\s+([0-9A-Za-z]+)')
# Heuristics that mean "the CPU is no longer executing the guest program".
_RE_HALT = re.compile(r'(?i)\b(halt(ed)?|stopped|breakpoint)\b')
_RE_PROMPT = re.compile(r'sim>\s*$')
# SIMH stop/step messages carry the program counter, e.g.
# "HALT instruction, PC: 017756 (WAIT)" or "Simulation stopped, PC: 001000".
_RE_PC = re.compile(r'(?i)\bPC:\s*([0-9A-Za-z]+)')

# Widget ids (across the 10 machine configs) that play the role of the
# address register / data register, so telemetry updates work generically
# without a per-machine mapping table.
_ADDR_WIDGET_IDS = ("address_lights", "address_display", "pc_lights",
                    "pc_display", "sar_lights", "ma_lights", "m_lights")
_DATA_WIDGET_IDS = ("data_lights", "data_display", "mb_lights", "ac_lights",
                    "display_lights")

# Status lamps driven generically from run / halt / alive state.  Only ids
# that actually exist in a given machine's config are ever touched, so the
# same mapping is safe across all 10 panels.
_STEADY_LEDS = ("power", "master")    # lit whenever the emulator process is alive
_CONSOLE_LEDS = ("console",)          # lit while stopped at the sim> console
_RUN_LEDS = ("run", "run_m")          # CPU is executing the guest program
_HALT_LEDS = ("halt", "pgm_stop", "io_halt", "wait", "hlta")  # CPU stopped

_RUN_VERBS = {"run", "go", "cont", "continue", "boot"}
_HALT_VERBS = {"halt", "reset", "step", "s"}


class MainWindow(QMainWindow):
    # Marshals raw SIMH stdout lines from the background reader thread
    # (see SIMHController) onto the GUI thread, where it's safe to touch
    # QWidgets such as the panel indicators.
    _rawOutput = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config_loader = ConfigLoader()
        self.simh_controller: SIMHController | None = None
        self.current_simulator: dict | None = None
        self.panel: UniversalPanel | None = None

        # Live emulator state tracked by the panel telemetry layer.
        self._is_running = False
        self._loaded_address = 0
        self._awaiting_reg_reply = False
        self._addr_step = 1
        self._dark = True

        self._rawOutput.connect(self._handle_simh_line)

        self._poll_timer = QTimer()
        self._poll_timer.setInterval(80)
        self._poll_timer.timeout.connect(self._poll_output)

        self.setWindowTitle("SIMH Universal Panel")
        self.setMinimumSize(900, 650)
        self.resize(1180, 880)

        self._init_ui()
        self._create_menu()
        self._create_toolbar()
        self._load_simulators()
        self._refresh_controls()

    # ------------------------------------------------------------------
    #  UI setup
    # ------------------------------------------------------------------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(8, 8, 8, 6)
        root_layout.setSpacing(6)
        central.setLayout(root_layout)

        # --- selector row -------------------------------------------------
        top = QHBoxLayout()
        lbl = QLabel("Эмулятор:")
        lbl.setStyleSheet("font-weight: bold; background: transparent;")
        top.addWidget(lbl)
        self.simulator_combo = QComboBox()
        self.simulator_combo.setMinimumWidth(240)
        self.simulator_combo.currentIndexChanged.connect(self._on_simulator_changed)
        top.addWidget(self.simulator_combo)

        # machine description shown next to the selector
        self._desc_label = QLabel("")
        self._desc_label.setObjectName("descLabel")
        self._desc_label.setStyleSheet(
            "color: #7fb8ff; background: transparent; font-style: italic;")
        top.addSpacing(10)
        top.addWidget(self._desc_label)

        top.addStretch()

        # Examine an arbitrary register / expression via SIMH (PC, R0, SP, …).
        reg_lbl = QLabel("Регистр:")
        reg_lbl.setStyleSheet("background: transparent;")
        top.addWidget(reg_lbl)
        self._reg_input = QLineEdit()
        self._reg_input.setPlaceholderText("напр. PC, R0, SP")
        self._reg_input.setFixedWidth(120)
        self._reg_input.returnPressed.connect(self._examine_register)
        top.addWidget(self._reg_input)
        self._reg_btn = QPushButton("Смотреть")
        self._reg_btn.clicked.connect(self._examine_register)
        top.addWidget(self._reg_btn)

        eq = QLabel("=")
        eq.setStyleSheet("background: transparent;")
        top.addWidget(eq)
        self._reg_val = QLineEdit()
        self._reg_val.setPlaceholderText("значение")
        self._reg_val.setFixedWidth(90)
        self._reg_val.returnPressed.connect(self._deposit_register)
        top.addWidget(self._reg_val)
        self._reg_dep_btn = QPushButton("Записать")
        self._reg_dep_btn.clicked.connect(self._deposit_register)
        top.addWidget(self._reg_dep_btn)
        top.addSpacing(12)

        self._status_pill = QLabel("Остановлен")
        self._status_pill.setObjectName("statusPill")
        self._set_pill(False)
        top.addWidget(self._status_pill)
        root_layout.addLayout(top)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #3a3f4b;")
        root_layout.addWidget(sep)

        # --- panel inside a scroll area (wide panels e.g. PDP-10 36-bit) --
        self._panel_scroll = QScrollArea()
        self._panel_scroll.setObjectName("panelScroll")
        self._panel_scroll.setWidgetResizable(True)
        self._panel_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._panel_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._panel_scroll.setFrameShape(QFrame.NoFrame)
        self._panel_scroll.setMinimumHeight(320)
        root_layout.addWidget(self._panel_scroll, stretch=3)

        # --- terminal -----------------------------------------------------
        self.terminal = TerminalWidget()
        self.terminal.setMinimumHeight(150)
        root_layout.addWidget(self.terminal, stretch=2)

        self.terminal.commandEntered.connect(self._on_command)
        self.terminal.setFocus()

    def _create_menu(self):
        mb = self.menuBar()

        emu = mb.addMenu("Эмулятор")
        self._act_start = QAction("Запустить  (Ctrl+F5)", self)
        self._act_start.setShortcut("Ctrl+F5")
        self._act_start.triggered.connect(self._start_emulator)
        emu.addAction(self._act_start)

        self._act_stop = QAction("Остановить  (Ctrl+F6)", self)
        self._act_stop.setShortcut("Ctrl+F6")
        self._act_stop.triggered.connect(self._stop_emulator)
        self._act_stop.setEnabled(False)
        emu.addAction(self._act_stop)

        emu.addSeparator()
        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        emu.addAction(act_exit)

        view = mb.addMenu("Вид")
        self._act_clear = QAction("Очистить терминал  (Ctrl+L)", self)
        self._act_clear.setShortcut("Ctrl+L")
        self._act_clear.triggered.connect(self._clear_terminal)
        view.addAction(self._act_clear)

        view.addSeparator()
        self._act_theme = QAction("Светлая тема", self)
        self._act_theme.triggered.connect(self._toggle_theme)
        view.addAction(self._act_theme)

        hlp = mb.addMenu("Помощь")
        act_about = QAction("О программе  (F1)", self)
        act_about.setShortcut("F1")
        act_about.triggered.connect(self._show_about)
        hlp.addAction(act_about)

    def _create_toolbar(self):
        tb = QToolBar("Управление")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        tb.addAction(self._act_start)
        tb.addAction(self._act_stop)
        sep = QWidget()
        sep.setFixedWidth(12)
        tb.addWidget(sep)
        tb.addAction(self._act_clear)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self._tb_hint = QLabel("Ctrl+F5 — запуск · Ctrl+F6 — стоп · Ctrl+L — очистка ")
        self._tb_hint.setStyleSheet("color: #6c7382; background: transparent;")
        tb.addWidget(self._tb_hint)

    # ------------------------------------------------------------------
    #  Helpers for visual state
    # ------------------------------------------------------------------

    def _set_pill(self, running: bool, name: str = ""):
        if running:
            self._status_pill.setText(f"● {name} работает")
            self._status_pill.setStyleSheet(
                "QLabel#statusPill { color: #06120a; background: #2ecc71;"
                " border-radius: 9px; padding: 3px 12px; font-weight: bold; }")
        else:
            self._status_pill.setText("○ Остановлен")
            self._status_pill.setStyleSheet(
                "QLabel#statusPill { color: #aab; background: #2b2f3a;"
                " border-radius: 9px; padding: 3px 12px; }")

    def _refresh_controls(self):
        running = bool(self.simh_controller and self.simh_controller.is_alive())
        self._act_start.setEnabled(not running)
        self._act_stop.setEnabled(running)
        self.simulator_combo.setEnabled(not running)

    # ------------------------------------------------------------------
    #  Simulator list & panel swap
    # ------------------------------------------------------------------

    def _load_simulators(self):
        cfg = self.config_loader.load_simh_config()
        for sim in cfg.get("simulators", []):
            self.simulator_combo.addItem(sim["name"], sim)
        if self.simulator_combo.count() > 0:
            self.simulator_combo.setCurrentIndex(0)

    def _on_simulator_changed(self, index):
        if index < 0:
            return
        self.current_simulator = self.simulator_combo.itemData(index)
        if not self.current_simulator:
            return
        self._desc_label.setText(self.current_simulator.get("description", ""))
        panel_cfg = self.config_loader.load_panel_config(self.current_simulator["name"])
        self._replace_panel(panel_cfg)

    def _replace_panel(self, panel_cfg: dict):
        if self.panel:
            self.panel.deleteLater()
            self.panel = None

        self._is_running = False
        self._loaded_address = 0
        self._awaiting_reg_reply = False
        # Address increment per EXAM/DEP step: byte-addressed machines advance
        # by the word size (PDP-11 → 2, VAX → 4); word-addressed ones by 1.
        self._addr_step = panel_cfg.get("addr_step", 1)

        self.panel = UniversalPanel(panel_cfg)
        self.panel.commandRequested.connect(self._on_panel_command)
        self.panel.switchChanged.connect(self._on_switch_changed)
        self._panel_scroll.setWidget(self.panel)

    # ------------------------------------------------------------------
    #  Emulator lifecycle
    # ------------------------------------------------------------------

    def _resolve_executable(self, exe: str) -> str | None:
        """Return an existing path for *exe*, trying a .exe suffix (Windows)."""
        candidates = [exe]
        if not exe.lower().endswith(".exe"):
            candidates.append(exe + ".exe")
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _start_emulator(self):
        if not self.current_simulator:
            QMessageBox.warning(self, "Ошибка", "Выберите эмулятор")
            return

        raw = self.current_simulator["executable"]
        exe = self._resolve_executable(raw)
        if exe is None:
            QMessageBox.warning(
                self, "Ошибка",
                f"Файл эмулятора не найден:\n{raw}\n\n"
                "Поместите бинарный файл SIMH в указанный путь.",
            )
            return

        opts = self.current_simulator.get("startup_options", [])
        self.simh_controller = SIMHController(exe, opts)
        # Route through the Qt signal (thread-safe) instead of calling the
        # terminal directly, so the same stream can also feed the panel
        # telemetry parser on the GUI thread.
        self.simh_controller.set_output_callback(self._rawOutput.emit)

        if self.simh_controller.start():
            name = self.current_simulator["name"]
            self._is_running = False
            self._loaded_address = 0
            self._awaiting_reg_reply = False
            if self.panel:
                self.panel.reset_all()
                # Powered on but halted at the console: light power/master and
                # the console/halt lamps so the panel isn't dark on start.
                self._set_running(False)
            self.terminal.schedule_output(f">>> {name} запущен\n")
            self._set_pill(True, name)
            self._refresh_controls()
            self._poll_timer.start()
        else:
            self.simh_controller = None
            QMessageBox.critical(self, "Ошибка", "Не удалось запустить эмулятор")

    def _stop_emulator(self):
        self._poll_timer.stop()
        if self.simh_controller:
            self.simh_controller.stop()
            self.simh_controller = None

        self.terminal.schedule_output(">>> Эмулятор остановлен\n")
        self._set_pill(False)
        self._is_running = False
        self._loaded_address = 0
        self._awaiting_reg_reply = False
        self._refresh_controls()

        if self.panel:
            self.panel.reset_all()

    def _poll_output(self):
        """Check if the emulator process has died unexpectedly."""
        if self.simh_controller and not self.simh_controller.is_alive():
            self.terminal.schedule_output(">>> Процесс эмулятора завершился\n")
            self._stop_emulator()

    # ------------------------------------------------------------------
    #  Live panel telemetry (RUN light + register displays)
    # ------------------------------------------------------------------

    def _handle_simh_line(self, text: str):
        """Runs on the GUI thread for every raw line SIMH prints to stdout."""
        self.terminal.schedule_output(text)
        self._process_telemetry(text)

    def _process_telemetry(self, text: str):
        if not self.panel:
            return
        line = text.strip()
        if not line:
            return

        # The CPU can stop on its own (HALT opcode, breakpoint, WRU) without
        # the user pressing the HALT button — catch that and turn RUN off.
        if self._is_running and (_RE_HALT.search(line) or _RE_PROMPT.search(line)):
            self._set_running(False)

        # SIMH stop / step lines report the program counter — reflect it on the
        # address (PC) lamps so STEP, HALT and end-of-RUN visibly move the panel,
        # not just the RUN light.
        mpc = _RE_PC.search(line)
        if mpc:
            pc = self._parse_num(mpc.group(1))
            if pc is not None:
                self._loaded_address = pc
                self._set_address(pc)

        # "<addr>: <value>" — the reply to EXAMINE/DEPOSIT (value is a number)
        # or the disassembly a single STEP echoes (value is a mnemonic, ignored).
        m = _RE_ADDR_VAL.match(line)
        if m:
            addr_val = self._parse_num(m.group(1))
            if addr_val is not None:
                self._set_address(addr_val)
                data_val = self._parse_num(m.group(2))
                if data_val is not None:
                    self._set_data(data_val)
                # Auto-increment the address after an EXAM/DEP reply, exactly
                # like the STEP behaviour of a real DEC front panel.
                if self._awaiting_reg_reply:
                    self._awaiting_reg_reply = False
                    self._loaded_address = addr_val + self._addr_step
                else:
                    self._loaded_address = addr_val

    def _set_led_group(self, led_ids, state: bool):
        """Set every LED in *led_ids* that actually exists on the panel."""
        if not self.panel:
            return
        for lid in led_ids:
            if self.panel.get_widget(lid):
                self.panel.set_led(lid, state)

    def _set_address(self, value: int):
        for wid in _ADDR_WIDGET_IDS:
            self.panel.set_register_value(wid, value)

    def _set_data(self, value: int):
        for wid in _DATA_WIDGET_IDS:
            self.panel.set_register_value(wid, value)

    @staticmethod
    def _parse_num(s: str):
        s = s.strip()
        try:
            if re.fullmatch(r'[0-7]+', s):
                return int(s, 8)
            if re.fullmatch(r'[0-9A-Fa-f]+', s):
                return int(s, 16)
            return int(s, 10)
        except ValueError:
            return None

    def _set_running(self, running: bool):
        self._is_running = running
        if not self.panel:
            return
        # This is only called while the process is alive, so the steady
        # power/master lamps stay lit; run vs. console/halt lamps mirror the CPU.
        self._set_led_group(_STEADY_LEDS, True)
        self._set_led_group(_RUN_LEDS, running)
        self._set_led_group(_HALT_LEDS, not running)
        self._set_led_group(_CONSOLE_LEDS, not running)

    def _track_run_state(self, command: str):
        parts = command.strip().lower().split()
        if not parts:
            return
        if parts[0] in _RUN_VERBS:
            self._set_running(True)
        elif parts[0] in _HALT_VERBS:
            self._set_running(False)

    # ------------------------------------------------------------------
    #  Command handling
    # ------------------------------------------------------------------

    def _on_command(self, command: str):
        if not command:
            return
        if self.simh_controller and self.simh_controller.is_alive():
            self._track_run_state(command)
            self.simh_controller.send_command(command)
            self.statusBar().showMessage(f"» {command}", 2000)
        else:
            self.terminal.schedule_output(
                ">>> Эмулятор не запущен. Меню «Эмулятор» → «Запустить»\n"
            )

    def _on_panel_command(self, command: str):
        if not self.panel:
            self._on_command(command)
            return

        sr_value = self.panel.get_switch_value("switch_reg")

        step = self._addr_step
        if command in ("examine", "examine +1"):
            addr = self._loaded_address + (step if command.endswith("+1") else 0)
            # SIMH expects a bare octal number ("1000"), not Python's "0o1000".
            command = f"examine {addr:o}"
            self._awaiting_reg_reply = True
        elif command in ("deposit", "deposit +1"):
            addr = self._loaded_address + (step if command.endswith("+1") else 0)
            command = f"deposit {addr:o} {sr_value:o}"
            # Show the written word on the data lamps, then advance the address
            # register (by the machine's word step) and display the incremented
            # address — like a real DEC front panel, where the address lamps
            # step on after each DEP.
            self._set_data(sr_value)
            self._loaded_address = addr + step
            self._set_address(self._loaded_address)
        elif command == "load_addr":
            self._loaded_address = sr_value
            self._set_address(sr_value)
            self.statusBar().showMessage(
                f"ADDR ← {sr_value:o}", 2000
            )
            return

        self._on_command(command)

    def _on_switch_changed(self, switch_id: str, value: int):
        self.statusBar().showMessage(
            f"Switch {switch_id} = {value:o}", 2000
        )

    # ------------------------------------------------------------------
    #  Misc
    # ------------------------------------------------------------------

    def _examine_register(self):
        """Examine any register / expression the user typed (PC, R0, SP, …)."""
        name = self._reg_input.text().strip()
        if not name:
            return
        if not (self.simh_controller and self.simh_controller.is_alive()):
            self.terminal.schedule_output(
                ">>> Эмулятор не запущен. Меню «Эмулятор» → «Запустить»\n")
            return
        # SIMH prints the reply ("PC: 001000") to stdout, which the telemetry
        # stream already echoes in the terminal.
        self.simh_controller.send_command(f"examine {name}")
        self.statusBar().showMessage(f"examine {name}", 2000)

    def _deposit_register(self):
        """Write a value into any register the user typed (deposit R0 <value>).

        Works for every emulator, since register names are handled by SIMH."""
        name = self._reg_input.text().strip()
        value = self._reg_val.text().strip()
        if not name or not value:
            self.statusBar().showMessage("Укажите регистр и значение", 2000)
            return
        if not (self.simh_controller and self.simh_controller.is_alive()):
            self.terminal.schedule_output(
                ">>> Эмулятор не запущен. Меню «Эмулятор» → «Запустить»\n")
            return
        self.simh_controller.send_command(f"deposit {name} {value}")
        # Read it straight back so the terminal confirms the new contents.
        self.simh_controller.send_command(f"examine {name}")
        self.statusBar().showMessage(f"deposit {name} = {value}", 2000)

    def _toggle_theme(self):
        self._dark = not self._dark
        app = QApplication.instance()
        if app:
            app.setStyleSheet(DARK_THEME if self._dark else LIGHT_THEME)
        theme_state.set_dark(self._dark)
        self._act_theme.setText("Светлая тема" if self._dark else "Тёмная тема")
        # Rebuild the current panel so its painted widgets (LED/register/switch
        # captions, group boxes) pick up the new palette, then restore the LEDs.
        idx = self.simulator_combo.currentIndex()
        if idx >= 0:
            self._on_simulator_changed(idx)
            if self.simh_controller and self.simh_controller.is_alive():
                self._set_running(self._is_running)

    def _clear_terminal(self):
        self.terminal.clear_terminal()

    def _show_about(self):
        count = self.simulator_combo.count()
        QMessageBox.about(
            self,
            "О программе",
            "<h3>SIMH Universal Panel</h3>"
            f"<p>Версия {APP_VERSION}</p>"
            "<p>Универсальная графическая панель управления<br>"
            "для эмуляторов семейства SIMH.</p>"
            f"<p>Поддерживается эмуляторов «из коробки»: <b>{count}</b><br>"
            "PDP-11, PDP-8, Altair 8800, VAX, PDP-1, PDP-10,<br>"
            "Nova, IBM 1401, HP 2100, Honeywell H316.</p>"
            "<p>Разработано для дипломной работы:<br>"
            "<i>Реализация универсальной панели<br>"
            "для эмуляторов Роберта Супника</i></p>",
        )

    def closeEvent(self, event):
        self._stop_emulator()
        event.accept()
