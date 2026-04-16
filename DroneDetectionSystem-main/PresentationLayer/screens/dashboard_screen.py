from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                             QFrame, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime

from BusinessLayer.track_business import TrackBusiness
from BusinessLayer.alert_business import AlertBusiness


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dashboard")
        self.stat_labels = {}
        self.setup_ui()
        self.refresh_data()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)  # Refresh every 5 seconds

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#38bdf8;")
        title.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(title)

        # Scroll area for responsiveness on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        # Stats grid (will be placed inside scroll area)
        self.stats_widget = QWidget()
        self.grid_layout = QGridLayout(self.stats_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)

        # Create stat cards
        stats = [
            ("total", "Total Detections", "0", "#22c55e"),
            ("active", "Active Drones", "0", "#38bdf8"),
            ("alerts", "Alerts Today", "0", "#ef4444"),
            ("status", "System Status", "Active", "#f59e0b")
        ]

        for i, (key, label, value, color) in enumerate(stats):
            card, val_label = self.create_stat_card(label, value, color)
            self.stat_labels[key] = val_label
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(card, row, col)

        scroll_layout.addWidget(self.stats_widget)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_stat_card(self, label, value, color):
        """Create a responsive stat card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.7);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 24px 20px;
            }
            QFrame:hover {
                background: rgba(30, 41, 59, 1);
                border: 1px solid rgba(56, 189, 248, 0.3);
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel(label)
        title.setStyleSheet("color:#94a3b8; font-size:15px; font-weight:500;")
        title.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(title)

        val_label = QLabel(str(value))
        val_label.setStyleSheet(f"font-size:42px; font-weight:bold; color:{color};")
        val_label.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(val_label)

        return card, val_label

    def refresh_data(self):
        try:
            all_tracks = TrackBusiness.get_all()
            self.stat_labels["total"].setText(str(len(all_tracks)))

            active_tracks = TrackBusiness.get_active()
            self.stat_labels["active"].setText(str(len(active_tracks)))

            today = datetime.now().date()
            recent_alerts = AlertBusiness.get_recent(500)
            alerts_today = sum(
                1 for a in recent_alerts
                if a.created_at and a.created_at.date() == today
            )
            self.stat_labels["alerts"].setText(str(alerts_today))

            self.stat_labels["status"].setText("● Online")
            self.stat_labels["status"].setStyleSheet("font-size:42px; font-weight:bold; color:#22c55e;")
        except Exception as e:
            print(f"Dashboard Error: {e}")
            self.stat_labels["status"].setText("● Offline")
            self.stat_labels["status"].setStyleSheet("font-size:42px; font-weight:bold; color:#ef4444;")

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()