from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from PresentationLayer.screens.dashboard_screen import DashboardScreen
from PresentationLayer.screens.live_feed_screen import LiveFeedScreen
from PresentationLayer.screens.logs_screen import LogsScreen
from PresentationLayer.screens.settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Detection System")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("""
            QMainWindow { background: #0f172a; }
        """)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- Modern Sidebar ----
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border-right: 1px solid #334155;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(10)

       
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 15)

        logo_text = QLabel("DroneDetected")
        logo_text.setFont(QFont("Arial", 16, QFont.Bold))
        logo_text.setStyleSheet("color: #38bdf8; background: transparent; border: none;")
        logo_text.setAlignment(Qt.AlignCenter)
        logo_text.setFixedHeight(40)  
        logo_layout.addWidget(logo_text)

        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addSpacing(20)

        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("🏠", "Dashboard", self.show_dashboard),
            ("📷", "Live Feed", self.show_live_feed),
            ("📋", "Event Logs", self.show_logs),
            ("⚙️", "Settings", self.show_settings)
        ]

        for icon, label, handler in nav_items:
            btn = QPushButton(f"{icon}  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    color: #94a3b8;
                    text-align: left;
                    padding: 12px 15px;
                    border: none;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 500;
                    background: transparent;
                }
                QPushButton:hover {
                    background: rgba(56, 189, 248, 0.1);
                    color: #f1f5f9;
                }
                QPushButton:checked {
                    background: #38bdf8;
                    color: white;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(handler)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

     
        

        main_layout.addWidget(sidebar)

        # ---- Content Area ----
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background: #0f172a;")

        self.dashboard = DashboardScreen()
        self.live_feed = LiveFeedScreen()
        self.logs = LogsScreen()
        self.settings = SettingsScreen()

        self.content_stack.addWidget(self.dashboard)
        self.content_stack.addWidget(self.live_feed)
        self.content_stack.addWidget(self.logs)
        self.content_stack.addWidget(self.settings)

        main_layout.addWidget(self.content_stack)

        # Set default active button and screen
        self.nav_buttons[0].setChecked(True)
        self.content_stack.setCurrentIndex(0)

    def show_dashboard(self):
        self.update_nav(0)
        self.content_stack.setCurrentIndex(0)

    def show_live_feed(self):
        self.update_nav(1)
        self.content_stack.setCurrentIndex(1)

    def show_logs(self):
        self.update_nav(2)
        self.content_stack.setCurrentIndex(2)

    def show_settings(self):
        self.update_nav(3)
        self.content_stack.setCurrentIndex(3)

    def update_nav(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)