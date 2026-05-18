import argparse
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from can_id_config import get_can_id
from can_udp_parser import MESSAGE_SPECS, parse_packet

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError as exc:
    raise SystemExit("PyQt5 is required. Install with: pip install PyQt5") from exc


TAB_ORDER = ["安全回路", "电机控制器", "转向系统", "EBS", "能量计", "ECU"]
SAFETY_LED_SOURCES = [
    ("锁存器1", "ebs_status"),
    ("锁存器2", "epos_heartbeat"),
    ("锁存器3", "ecu_msg"),
    ("锁存器4", "amk_actual_lf"),
]

# Toy-like VI palette based on the HRT 26D Smart Falcon mascot design.
# The UI keeps the black base, adds more mascot-gray plastic panels, and uses
# teal/orange/red as toy-block accent colors.
VI_BLACK = "#090909"
VI_CHARCOAL = "#141718"
VI_PANEL = "#1D2324"
VI_PANEL_2 = "#252B2D"
VI_PANEL_3 = "#32383A"
VI_PANEL_4 = "#3F4648"
VI_GRID = "#5A5A5A"
VI_TEAL = "#5BC5C3"
VI_TEAL_BRIGHT = "#38E8E3"
VI_TEAL_DARK = "#178E8C"
VI_ORANGE = "#FF8100"
VI_ORANGE_DARK = "#D37B1D"
VI_RED = "#A6361F"
VI_RED_BRIGHT = "#D94B2B"
VI_LIGHT = "#FFFFFF"
VI_SOFT_WHITE = "#F4F6F6"
VI_SILVER = "#C4C4C4"
VI_GRAY = "#5A5A5A"
VI_DARK_TEXT = "#111515"


def pick_first_available_font(candidates: List[str]) -> str:
    families = set(QtGui.QFontDatabase().families())
    for name in candidates:
        if name in families:
            return name
    return QtWidgets.QApplication.font().family()


def resolve_ui_fonts() -> Tuple[str, str]:
    if sys.platform == "darwin":
        english_candidates = ["Comic Sans MS", "Comic Sans", "Chalkboard SE", "Arial Rounded MT Bold", "Arial"]
        chinese_candidates = ["PingFang SC", "Hiragino Sans GB", "STHeiti", "Heiti SC", "Arial Unicode MS"]
    elif sys.platform.startswith("win"):
        english_candidates = ["Comic Sans MS", "Comic Sans", "Arial Rounded MT Bold", "Arial"]
        chinese_candidates = ["YouYuan", "幼圆", "Microsoft YaHei", "SimHei"]
    else:
        english_candidates = ["Comic Sans MS", "Comic Sans", "Arial Rounded MT Bold", "Arial"]
        chinese_candidates = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "Microsoft YaHei", "SimHei"]

    return (
        pick_first_available_font(english_candidates),
        pick_first_available_font(chinese_candidates),
    )


@dataclass
class MessageRowBinding:
    raw_item: QtWidgets.QTableWidgetItem
    parsed_item: QtWidgets.QTableWidgetItem
    led: QtWidgets.QLabel


def set_led(led: QtWidgets.QLabel, ok: bool) -> None:
    size = min(led.width(), led.height())
    radius = max(size // 2 - 1, 1)
    color = VI_TEAL_BRIGHT if ok else VI_RED_BRIGHT
    ring = VI_SOFT_WHITE if ok else VI_ORANGE
    shadow = VI_TEAL_DARK if ok else VI_RED
    led.setStyleSheet(
        "QLabel {"
        f"background-color: {color};"
        f"border: 3px solid {ring};"
        f"border-radius: {radius}px;"
        f"padding: 1px;"
        f"selection-background-color: {shadow};"
        "}"
    )


def create_centered_led(size: int, background_color: str = VI_PANEL_2) -> Tuple[QtWidgets.QLabel, QtWidgets.QWidget]:
    led = QtWidgets.QLabel()
    led.setFixedSize(size, size)
    holder = QtWidgets.QFrame()
    holder.setObjectName("statusCell")
    holder.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    holder.setAutoFillBackground(True)
    palette = holder.palette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(background_color))
    holder.setPalette(palette)
    holder.setStyleSheet(
        f"QFrame#statusCell {{ background-color: {background_color}; border: none; margin: 0px; padding: 0px; }}"
    )
    holder_layout = QtWidgets.QHBoxLayout(holder)
    holder_layout.setContentsMargins(0, 0, 0, 0)
    holder_layout.setSpacing(0)
    holder_layout.addStretch(1)
    holder_layout.addWidget(led)
    holder_layout.addStretch(1)
    return led, holder


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def format_decoded_text(decoded: Dict[str, object]) -> str:
    """Format decoded CAN signals as plain table text, one signal per line."""
    if not decoded:
        return "-"
    return "\n".join(f"{key}: {_format_value(value)}" for key, value in decoded.items())


class UdpReceiverThread(QtCore.QThread):
    packet_received = QtCore.pyqtSignal(dict)
    packet_error = QtCore.pyqtSignal(str)
    bind_failed = QtCore.pyqtSignal(str)

    def __init__(self, ip: str, port: int):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        try:
            sock.bind((self.ip, self.port))
        except OSError as exc:
            sock.close()
            self.bind_failed.emit(str(exc))
            return

        try:
            while not self.isInterruptionRequested():
                try:
                    packet, _addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except OSError as exc:
                    self.packet_error.emit(str(exc))
                    break

                try:
                    result = parse_packet(packet)
                    self.packet_received.emit(result)
                except Exception as exc:
                    self.packet_error.emit(str(exc))
        finally:
            sock.close()


class CanUdpMonitorWindow(QtWidgets.QMainWindow):
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.setWindowTitle("Ann Data Analyser")
        icon_path = Path(__file__).resolve().parent / "icon" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self.setMinimumSize(960, 640)
        screen = QtWidgets.QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            width = min(area.width(), max(1100, int(area.width() * 0.88)))
            height = min(area.height(), max(760, int(area.height() * 0.88)))
            self.resize(width, height)
        else:
            self.resize(1280, 800)

        self.settings = QtCore.QSettings("AnnDataAnalyser", "CanUdpGui")
        self.receiver = None

        self.last_rx: Dict[str, float] = {}
        self.latest_display: Dict[str, Dict[str, object]] = {}
        self.bindings: Dict[str, List[MessageRowBinding]] = {}
        self.safety_leds: Dict[str, QtWidgets.QLabel] = {}
        self.data_tables: List[QtWidgets.QTableWidget] = []

        self.stats_start_time = time.monotonic()
        self.total_udp_packets = 0
        self.total_can_frames = 0
        self.receiving_active = False

        self.root = QtWidgets.QWidget()
        self.root.setObjectName("appRoot")
        self.root_layout = QtWidgets.QVBoxLayout(self.root)
        self.root_layout.setContentsMargins(12, 12, 12, 8)
        self.root_layout.setSpacing(10)
        self.setCentralWidget(self.root)

        self._build_top_controls()
        self._build_content_area()
        self._load_last_connection(default_ip=ip, default_port=port)

        self.status = self.statusBar()
        self.status.showMessage("未连接")

        self.ui_timer = QtCore.QTimer(self)
        self.ui_timer.setInterval(500)
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()

    def _build_top_controls(self) -> None:
        control_row = QtWidgets.QHBoxLayout()
        control_row.setSpacing(12)
        self.ip_input = QtWidgets.QLineEdit()
        self.ip_input.setObjectName("connectionInput")
        self.port_input = QtWidgets.QLineEdit()
        self.port_input.setObjectName("connectionInput")
        self.port_input.setValidator(QtGui.QIntValidator(1, 65535))
        self.connect_button = QtWidgets.QPushButton("连接")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        ip_label = QtWidgets.QLabel("IP:")
        ip_label.setObjectName("connectionLabel")
        port_label = QtWidgets.QLabel("PORT:")
        port_label.setObjectName("connectionLabel")

        for widget in (ip_label, self.ip_input, port_label, self.port_input, self.connect_button):
            widget.setFixedHeight(56)

        control_row.addWidget(ip_label)
        control_row.addWidget(self.ip_input, 1)
        control_row.addWidget(port_label)
        control_row.addWidget(self.port_input)
        control_row.addWidget(self.connect_button)
        self.root_layout.addLayout(control_row)

    def _build_content_area(self) -> None:
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.tabs.setTabPosition(QtWidgets.QTabWidget.South)

        self._build_tabs()
        self.stats_panel = self._build_stats_sidebar()

        # The tab widget includes the bottom tab bar in its total height, while the
        # visible table frame sits inside the tab page. Put the right sidebar in a
        # wrapper with matching top/bottom margins so its border aligns with the
        # table frame instead of the whole tab widget.
        self.stats_panel_wrapper = QtWidgets.QWidget()
        self.stats_panel_wrapper.setObjectName("statsPanelWrapper")
        self.stats_panel_wrapper.setFixedWidth(450)
        stats_wrapper_layout = QtWidgets.QVBoxLayout(self.stats_panel_wrapper)
        stats_wrapper_layout.setContentsMargins(0, 8, 0, 64)
        stats_wrapper_layout.setSpacing(0)
        stats_wrapper_layout.addWidget(self.stats_panel, 1)

        content_row = QtWidgets.QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(10)
        content_row.addWidget(self.tabs, 1)
        content_row.addWidget(self.stats_panel_wrapper)
        self.root_layout.addLayout(content_row, 1)

    def _build_tabs(self) -> None:
        specs_by_tab: Dict[str, List[Dict[str, object]]] = {name: [] for name in TAB_ORDER}
        for spec in MESSAGE_SPECS:
            tab_name = str(spec["tab"])
            specs_by_tab.setdefault(tab_name, []).append(spec)

        for tab_name in TAB_ORDER:
            if tab_name == "安全回路":
                self._build_safety_tab()
                continue

            tab_specs = specs_by_tab.get(tab_name, [])
            table = QtWidgets.QTableWidget(len(tab_specs), 5)
            table.setObjectName("dataTable")
            table.setHorizontalHeaderLabels(["ID号", "数据项", "原始信息", "解析后信息", "状态"])
            header = table.horizontalHeader()
            header.setDefaultAlignment(QtCore.Qt.AlignCenter)
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
            table.verticalHeader().setVisible(False)
            table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            table.setWordWrap(True)
            table.setAlternatingRowColors(True)
            table.setShowGrid(True)
            table.setFrameShape(QtWidgets.QFrame.NoFrame)
            table.setLineWidth(0)
            table.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            table.viewport().setAttribute(QtCore.Qt.WA_StyledBackground, True)
            table.setViewportMargins(0, 0, 0, 0)

            for row, spec in enumerate(tab_specs):
                message_key = str(spec["key"])
                can_id = get_can_id(message_key)
                name_item = QtWidgets.QTableWidgetItem(str(spec["name"]))
                id_item = QtWidgets.QTableWidgetItem(hex(can_id))
                raw_item = QtWidgets.QTableWidgetItem("-")
                parsed_item = QtWidgets.QTableWidgetItem("-")
                parsed_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

                row_color = VI_PANEL_2 if row % 2 == 0 else VI_PANEL_3
                row_background = QtGui.QBrush(QtGui.QColor(row_color))
                for item in (id_item, name_item, raw_item, parsed_item):
                    item.setBackground(row_background)
                    item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                id_item.setForeground(QtGui.QBrush(QtGui.QColor(VI_TEAL_BRIGHT)))
                name_item.setForeground(QtGui.QBrush(QtGui.QColor(VI_ORANGE)))
                raw_item.setForeground(QtGui.QBrush(QtGui.QColor(VI_SILVER)))
                parsed_item.setForeground(QtGui.QBrush(QtGui.QColor(VI_SOFT_WHITE)))

                led, led_holder = create_centered_led(28, row_color)
                set_led(led, False)

                table.setItem(row, 0, id_item)
                table.setItem(row, 1, name_item)
                table.setItem(row, 2, raw_item)
                table.setItem(row, 3, parsed_item)
                table.setCellWidget(row, 4, led_holder)

                self.bindings.setdefault(message_key, []).append(
                    MessageRowBinding(
                        raw_item=raw_item,
                        parsed_item=parsed_item,
                        led=led,
                    )
                )

            page = QtWidgets.QWidget()
            page.setObjectName("tablePage")
            page.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            layout = QtWidgets.QVBoxLayout(page)
            layout.setContentsMargins(8, 8, 8, 4)
            layout.setSpacing(0)

            table_shell = QtWidgets.QFrame()
            table_shell.setObjectName("tableShell")
            table_shell.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            shell_layout = QtWidgets.QVBoxLayout(table_shell)
            shell_layout.setContentsMargins(4, 4, 4, 4)
            shell_layout.setSpacing(0)
            shell_layout.addWidget(table)
            layout.addWidget(table_shell)

            self.tabs.addTab(page, tab_name)
            self.data_tables.append(table)

    def _build_safety_tab(self) -> None:
        page = QtWidgets.QWidget()
        page.setObjectName("tablePage")
        page.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(0)

        shell = QtWidgets.QFrame()
        shell.setObjectName("tableShell")
        shell.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        shell_layout = QtWidgets.QVBoxLayout(shell)
        shell_layout.setContentsMargins(28, 20, 28, 20)
        shell_layout.setSpacing(0)

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        left_group = QtWidgets.QVBoxLayout()
        left_group.setSpacing(18)
        left_group.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        right_group = QtWidgets.QVBoxLayout()
        right_group.setSpacing(18)
        right_group.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        for idx, (display_name, message_key) in enumerate(SAFETY_LED_SOURCES):
            led, holder = create_centered_led(44, VI_PANEL_2)
            set_led(led, False)
            holder.setFixedWidth(180)

            item_layout = QtWidgets.QHBoxLayout()
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(10)
            label = QtWidgets.QLabel(display_name)
            label.setAlignment(QtCore.Qt.AlignVCenter)
            label.setStyleSheet("background: transparent;")
            item_layout.addWidget(led)
            item_layout.addWidget(label)
            item_layout.addStretch(1)

            wrap = QtWidgets.QWidget()
            wrap.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            wrap.setStyleSheet("background: transparent; border: none;")
            wrap.setLayout(item_layout)
            if idx < 2:
                left_group.addWidget(wrap, 0, QtCore.Qt.AlignLeft)
            else:
                right_group.addWidget(wrap, 0, QtCore.Qt.AlignRight)

            self.safety_leds[message_key] = led

        middle_placeholder = QtWidgets.QLabel("图片预留区域")
        middle_placeholder.setAlignment(QtCore.Qt.AlignCenter)
        middle_placeholder.setStyleSheet(
            f"color: {VI_SILVER}; border: 2px dashed {VI_GRID}; border-radius: 14px; background: transparent;"
        )
        middle_placeholder.setMinimumSize(300, 220)

        row.addLayout(left_group, 1)
        row.addStretch(1)
        row.addWidget(middle_placeholder, 0, QtCore.Qt.AlignCenter)
        row.addStretch(1)
        row.addLayout(right_group, 1)

        shell_layout.addStretch(1)
        shell_layout.addLayout(row)
        shell_layout.addStretch(1)

        layout.addWidget(shell)
        self.tabs.addTab(page, "安全回路")

    def _build_stats_sidebar(self) -> QtWidgets.QFrame:
        panel = QtWidgets.QFrame()
        panel.setObjectName("statsPanel")
        panel.setFixedWidth(450)
        panel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 6)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("通信状态")
        title.setObjectName("statsTitle")
        title.setAlignment(QtCore.Qt.AlignCenter)
        self.stats_rate_udp_label = QtWidgets.QLabel("UDP接收速率: 0.0 package/s")
        self.stats_rate_can_label = QtWidgets.QLabel("CAN接收速率: 0.0 frame/s")
        self.stats_total_can_label = QtWidgets.QLabel("CAN报文总数: 0")
        self.stats_total_udp_label = QtWidgets.QLabel("UDP报文总数: 0")
        self.stats_uptime_label = QtWidgets.QLabel("运行时长: 0.0 s")
        self.stats_last_packet_label = QtWidgets.QLabel("最近接收时间: -")

        metric_labels = [
            (self.stats_rate_udp_label, "statsMetricTeal"),
            (self.stats_rate_can_label, "statsMetricOrange"),
            (self.stats_total_can_label, "statsMetricGray"),
            (self.stats_total_udp_label, "statsMetricRed"),
            (self.stats_uptime_label, "statsMetricTeal"),
            (self.stats_last_packet_label, "statsMetricOrange"),
        ]

        layout.addWidget(title)
        for label, object_name in metric_labels:
            label.setObjectName(object_name)
            label.setWordWrap(False)
            label.setMinimumHeight(52)
            layout.addWidget(label)

        layout.addStretch(1)

        logo_path = Path(__file__).resolve().parent / "icon" / "logo.png"
        self.mascot_logo = QtWidgets.QLabel()
        self.mascot_logo.setObjectName("mascotLogo")
        self.mascot_logo.setFixedSize(250, 250)
        self.mascot_logo.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        if logo_path.exists():
            logo_pixmap = QtGui.QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                self.mascot_logo.setPixmap(
                    logo_pixmap.scaled(
                        238,
                        238,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )
                )
            else:
                self.mascot_logo.setText("LOGO")
        else:
            self.mascot_logo.setText("icon/logo.png")
        layout.addWidget(self.mascot_logo, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.mascot_title = QtWidgets.QLabel("Ann Data Analyser")
        self.mascot_title.setObjectName("mascotTitle")
        self.mascot_title.setAlignment(QtCore.Qt.AlignCenter)
        self.mascot_title.setFixedWidth(430)
        self.mascot_title.setFixedHeight(44)
        layout.addSpacing(0)
        layout.addWidget(self.mascot_title, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        return panel

    def _load_last_connection(self, default_ip: str, default_port: int) -> None:
        saved_ip = self.settings.value("udp/ip", default_ip, type=str)
        saved_port = self.settings.value("udp/port", str(default_port), type=str)
        self.ip_input.setText(saved_ip)
        self.port_input.setText(saved_port)

    def _save_last_connection(self) -> None:
        self.settings.setValue("udp/ip", self.ip_input.text().strip())
        self.settings.setValue("udp/port", self.port_input.text().strip())
        self.settings.sync()

    def _reset_stats(self) -> None:
        self.stats_start_time = time.monotonic()
        self.total_udp_packets = 0
        self.total_can_frames = 0
        self.stats_last_packet_label.setText("最近接收时间: -")

    def _stop_receiver(self) -> None:
        if self.receiver is None:
            self.receiving_active = False
            return
        self.receiver.requestInterruption()
        self.receiver.wait(1500)
        self.receiver = None
        self.receiving_active = False
        self.connect_button.setText("连接")

    @QtCore.pyqtSlot()
    def on_connect_clicked(self) -> None:
        if self.receiver is not None and self.receiver.isRunning():
            self._stop_receiver()
            self.status.showMessage("已断开")
            return

        ip = self.ip_input.text().strip()
        port_text = self.port_input.text().strip()
        if not ip:
            QtWidgets.QMessageBox.warning(self, "输入错误", "IP 不能为空。")
            return
        if not port_text:
            QtWidgets.QMessageBox.warning(self, "输入错误", "Port 不能为空。")
            return

        try:
            port = int(port_text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "输入错误", "Port 必须是数字。")
            return
        if port <= 0 or port > 65535:
            QtWidgets.QMessageBox.warning(self, "输入错误", "Port 范围必须是 1~65535。")
            return

        self._save_last_connection()
        self._reset_stats()
        self.receiver = UdpReceiverThread(ip, port)
        self.receiver.packet_received.connect(self.on_packet_received)
        self.receiver.packet_error.connect(self.on_packet_error)
        self.receiver.bind_failed.connect(self.on_bind_failed)
        self.receiver.start()
        self.receiving_active = True
        self.connect_button.setText("断开")
        self.status.showMessage(f"监听中: {ip}:{port}")

    @QtCore.pyqtSlot(dict)
    def on_packet_received(self, packet: dict) -> None:
        frames = packet.get("frames", [])
        self.total_udp_packets += 1
        self.total_can_frames += len(frames)
        self.stats_last_packet_label.setText(
            f"最近接收时间: {time.strftime('%H:%M:%S', time.localtime())}"
        )

        for frame in frames:
            message_key = frame.get("message_key")
            if not message_key or message_key not in self.bindings:
                continue
            self.last_rx[message_key] = time.monotonic()
            self.latest_display[message_key] = {
                "raw_hex": str(frame.get("data_hex", "-")),
                "decoded": frame.get("decoded", {}),
            }

    @QtCore.pyqtSlot(str)
    def on_packet_error(self, error: str) -> None:
        self.status.showMessage(f"解析/接收异常: {error}")

    @QtCore.pyqtSlot(str)
    def on_bind_failed(self, error: str) -> None:
        self._stop_receiver()
        self.status.showMessage("未连接")
        QtWidgets.QMessageBox.critical(
            self,
            "连接失败",
            f"无法监听指定地址，请检查 IP/端口是否可用：\n{error}",
        )

    def refresh_ui(self) -> None:
        table_needs_resize = False
        for key, payload in self.latest_display.items():
            raw_hex = str(payload.get("raw_hex", "-"))
            decoded = payload.get("decoded", {})
            if not isinstance(decoded, dict):
                decoded = {}
            for bind in self.bindings.get(key, []):
                bind.raw_item.setText(raw_hex)
                bind.parsed_item.setText(format_decoded_text(decoded))
                table_needs_resize = True

        if table_needs_resize:
            for table in self.data_tables:
                table.resizeRowsToContents()

        now = time.monotonic()
        for key, binds in self.bindings.items():
            ok = (now - self.last_rx.get(key, 0.0)) <= 2.0
            for bind in binds:
                set_led(bind.led, ok)

        for source_key, led in self.safety_leds.items():
            ok = (now - self.last_rx.get(source_key, 0.0)) <= 2.0
            set_led(led, ok)

        elapsed = max(now - self.stats_start_time, 1e-6)
        if self.receiving_active:
            udp_rate = self.total_udp_packets / elapsed
            can_rate = self.total_can_frames / elapsed
        else:
            udp_rate = 0.0
            can_rate = 0.0
        self.stats_rate_udp_label.setText(f"UDP接收速率: {udp_rate:.1f} package/s")
        self.stats_rate_can_label.setText(f"CAN接收速率: {can_rate:.1f} frame/s")
        self.stats_total_can_label.setText(f"CAN报文总数: {self.total_can_frames}")
        self.stats_total_udp_label.setText(f"UDP报文总数: {self.total_udp_packets}")
        self.stats_uptime_label.setText(f"运行时长: {elapsed:.1f} s")

    def closeEvent(self, event):  # type: ignore[override]
        self._save_last_connection()
        self._stop_receiver()
        super().closeEvent(event)


def main() -> None:
    parser = argparse.ArgumentParser(description="PyQt CAN UDP monitor GUI.")
    parser.add_argument("--ip", default="127.0.0.1", help="Local bind IP")
    parser.add_argument("--port", type=int, default=5005, help="Local bind port")
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    english_font, chinese_font = resolve_ui_fonts()
    font_stack = f'"{english_font}", "{chinese_font}", "sans-serif"'
    app.setFont(QtGui.QFont(english_font, 13, QtGui.QFont.Bold))
    icon_path = Path(__file__).resolve().parent / "icon" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    app.setStyleSheet(
        f"""
        QMainWindow {{
            background-color: {VI_BLACK};
        }}
        QWidget#appRoot {{
            background-color: {VI_BLACK};
        }}
        QWidget {{
            background-color: {VI_BLACK};
            color: {VI_SOFT_WHITE};
            font-family: {font_stack};
            font-size: 20px;
            font-weight: 900;
        }}
        QLabel {{
            color: {VI_SOFT_WHITE};
            background: transparent;
        }}
        QLabel#connectionLabel {{
            color: {VI_SOFT_WHITE};
            background-color: {VI_TEAL};
            border: 4px solid {VI_SOFT_WHITE};
            border-radius: 28px;
            padding: 0px 18px;
            font-size: 21px;
            min-width: 58px;
        }}
        QLabel#statsTitle {{
            color: {VI_DARK_TEXT};
            background-color: {VI_SOFT_WHITE};
            border: 4px solid {VI_TEAL};
            border-bottom: 7px solid {VI_ORANGE};
            border-radius: 24px;
            padding: 12px 14px;
            font-size: 24px;
            letter-spacing: 1px;
        }}
        QLabel#statsMetricTeal, QLabel#statsMetricOrange,
        QLabel#statsMetricGray, QLabel#statsMetricRed {{
            color: {VI_SOFT_WHITE};
            background-color: {VI_PANEL_2};
            border: 2px solid {VI_GRID};
            border-radius: 22px;
            padding: 12px 13px;
            font-size: 21px;
        }}
        QLabel#statsMetricTeal {{
            border-left: 10px solid {VI_TEAL};
            background-color: #2B3839;
        }}
        QLabel#statsMetricOrange {{
            border-left: 10px solid {VI_ORANGE};
            background-color: #3A3127;
        }}
        QLabel#statsMetricGray {{
            border-left: 10px solid {VI_SILVER};
            background-color: {VI_PANEL_4};
        }}
        QLabel#statsMetricRed {{
            border-left: 10px solid {VI_RED_BRIGHT};
            background-color: #3A2825;
        }}
        QFrame#statsPanel {{
            background-color: {VI_PANEL};
            border: 4px solid {VI_GRAY};
            border-top: 6px solid {VI_TEAL};
            border-radius: 30px;
        }}
        QLabel#mascotLogo {{
            background: transparent;
            border: none;
            border-radius: 0px;
            padding: 0px;
            color: {VI_SILVER};
        }}
        QLabel#mascotTitle {{
            background: transparent;
            border: none;
            color: {VI_SOFT_WHITE};
            font-family: {font_stack};
            font-size: 34px;
            font-weight: 900;
            padding: 0px;
        }}
        QLineEdit#connectionInput, QLineEdit {{
            background-color: {VI_SOFT_WHITE};
            color: {VI_DARK_TEXT};
            border: 4px solid {VI_GRAY};
            border-radius: 28px;
            padding: 0px 18px;
            font-size: 21px;
            selection-background-color: {VI_TEAL};
            selection-color: {VI_DARK_TEXT};
        }}
        QLineEdit#connectionInput:focus, QLineEdit:focus {{
            border: 4px solid {VI_TEAL};
            background-color: {VI_LIGHT};
        }}
        QPushButton {{
            background-color: {VI_PANEL_4};
            color: {VI_SOFT_WHITE};
            border: 4px solid {VI_SILVER};
            border-radius: 28px;
            padding: 0px 22px;
            font-size: 21px;
        }}
        QPushButton#connectButton {{
            background-color: {VI_ORANGE};
            color: {VI_SOFT_WHITE};
            border: 4px solid {VI_SOFT_WHITE};
        }}
        QPushButton:hover {{
            background-color: {VI_TEAL};
            color: {VI_DARK_TEXT};
            border-color: {VI_SOFT_WHITE};
        }}
        QPushButton#connectButton:hover {{
            background-color: {VI_TEAL_BRIGHT};
            color: {VI_SOFT_WHITE};
            border-color: {VI_LIGHT};
        }}
        QPushButton:pressed, QPushButton#connectButton:pressed {{
            background-color: {VI_RED};
            color: {VI_SOFT_WHITE};
            border-color: {VI_ORANGE};
        }}
        QTabWidget#mainTabs {{
            background: transparent;
            border: none;
        }}
        QTabWidget#mainTabs::pane {{
            border: none;
            border-radius: 0px;
            margin-top: 3px;
            margin-bottom: 0px;
            background: transparent;
        }}
        QWidget#tablePage {{
            background: transparent;
            border: none;
            border-radius: 0px;
        }}
        QTabWidget#mainTabs QStackedWidget {{
            background: transparent;
            border: none;
        }}
        QTabWidget#mainTabs::tab-bar {{
            left: 4px;
        }}
        QTabBar::tab {{
            background-color: {VI_PANEL_3};
            color: {VI_SILVER};
            border: 3px solid {VI_GRID};
            border-bottom: 5px solid {VI_GRAY};
            border-radius: 24px;
            padding: 10px 20px;
            margin-right: 7px;
            margin-top: 3px;
            font-size: 20px;
        }}
        QTabBar::tab:hover {{
            color: {VI_LIGHT};
            background-color: {VI_PANEL_4};
            border-color: {VI_TEAL};
            border-bottom-color: {VI_ORANGE};
        }}
        QTabBar::tab:selected {{
            background-color: {VI_TEAL};
            color: {VI_DARK_TEXT};
            border: 4px solid {VI_SOFT_WHITE};
            border-bottom: 7px solid {VI_ORANGE};
        }}
        QFrame#tableShell {{
            background-color: {VI_PANEL_2};
            border: 4px solid {VI_GRAY};
            border-radius: 30px;
        }}
        QTableWidget#dataTable {{
            background-color: {VI_PANEL_2};
            alternate-background-color: {VI_PANEL_3};
            color: {VI_SOFT_WHITE};
            gridline-color: {VI_GRID};
            border: 2px solid {VI_GRID};
            border-radius: 20px;
            selection-background-color: {VI_TEAL_DARK};
            selection-color: {VI_LIGHT};
            font-size: 20px;
        }}
        QTableWidget#dataTable::viewport {{
            background-color: {VI_PANEL_2};
            border-radius: 20px;
        }}
        QTableView#dataTable {{
            background-color: {VI_PANEL_2};
        }}
        QAbstractScrollArea::corner {{
            background-color: {VI_PANEL_2};
            border: none;
        }}
        QHeaderView {{
            background-color: {VI_PANEL_2};
            border-radius: 18px;
        }}
        QFrame#statusCell, QWidget#statusCell {{
            border: none;
        }}
        QTableWidget#dataTable::item {{
            border-bottom: 1px solid {VI_GRID};
            padding: 10px 12px;
            font-size: 20px;
        }}
        QTableWidget#dataTable::item:selected {{
            background-color: {VI_TEAL_DARK};
            color: {VI_LIGHT};
        }}
        QHeaderView::section {{
            background-color: {VI_PANEL_4};
            color: {VI_SOFT_WHITE};
            border: 2px solid {VI_GRID};
            border-top: 5px solid {VI_ORANGE};
            border-bottom: 6px solid {VI_TEAL};
            padding: 10px;
            font-size: 20px;
        }}
        QHeaderView::section:first {{
            border-top-left-radius: 14px;
        }}
        QHeaderView::section:last {{
            border-top-right-radius: 14px;
        }}
        QTableCornerButton::section {{
            background-color: {VI_PANEL_3};
            border: 2px solid {VI_GRID};
        }}
        QScrollBar:vertical {{
            background-color: {VI_CHARCOAL};
            width: 15px;
            margin: 0;
            border: 2px solid {VI_GRID};
            border-radius: 10px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {VI_TEAL};
            min-height: 30px;
            border-radius: 9px;
            border: 2px solid {VI_SOFT_WHITE};
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {VI_ORANGE};
        }}
        QScrollBar:horizontal {{
            background-color: {VI_CHARCOAL};
            height: 15px;
            margin: 0;
            border: 2px solid {VI_GRID};
            border-radius: 10px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {VI_TEAL};
            min-width: 30px;
            border-radius: 9px;
            border: 2px solid {VI_SOFT_WHITE};
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {VI_ORANGE};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0;
            height: 0;
        }}
        QStatusBar {{
            background-color: {VI_PANEL_3};
            color: {VI_TEAL_BRIGHT};
            border-top: 4px solid {VI_GRAY};
            padding: 4px;
            font-size: 20px;
        }}
        QStatusBar::item {{
            border: none;
        }}
        QMessageBox {{
            background-color: {VI_PANEL_2};
        }}
        QToolTip {{
            background-color: {VI_PANEL_3};
            color: {VI_LIGHT};
            border: 2px solid {VI_TEAL};
        }}
        """
    )
    window = CanUdpMonitorWindow(args.ip, args.port)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
