from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                             QFrame, QHBoxLayout, QPushButton)
from PyQt5.QtCore import QTimer, Qt
from BusinessLayer.alert_business import AlertBusiness

class LogsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("logs")
        self.setup_ui()
        self.load_logs()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs)
        self.timer.start(10000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Event Logs")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#38bdf8;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #38bdf8;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0ea5e9; }
        """)
        refresh_btn.clicked.connect(self.load_logs)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        # Scroll Area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)

    def create_alert_card(self, alert):
        """Create a stylish card for an alert"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.8);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 16px;
            }
            QFrame:hover {
                background: rgba(30, 41, 59, 1);
                border: 1px solid rgba(56, 189, 248, 0.3);
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        # Top row: Alert type + time
        top_row = QHBoxLayout()
        
        # Alert type with colored badge
        alert_badge = QLabel(f" {alert.type_name} ")
        alert_badge.setStyleSheet(f"""
            QLabel {{
                background: {self.get_badge_color(alert.type_code)};
                color: white;
                border-radius: 20px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        top_row.addWidget(alert_badge)
        top_row.addStretch()
        
        # Time
        time_str = alert.created_at.strftime("%Y-%m-%d %H:%M:%S") if alert.created_at else "-"
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        top_row.addWidget(time_label)
        card_layout.addLayout(top_row)

        # Middle row: Track info
        track_label = QLabel(f"Track #{alert.track_id}")
        track_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        card_layout.addWidget(track_label)

        # Bottom row: Severity + Status
        bottom_row = QHBoxLayout()
        
        severity = "High" if alert.type_code == "NEW" else "Medium"
        severity_label = QLabel(f"Severity: {severity}")
        severity_label.setStyleSheet(f"color: {'#ef4444' if severity == 'High' else '#f59e0b'}; font-size: 13px;")
        bottom_row.addWidget(severity_label)
        bottom_row.addStretch()
        
        status_label = QLabel("Unacknowledged")
        status_label.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
        bottom_row.addWidget(status_label)
        card_layout.addLayout(bottom_row)

        return card

    def get_badge_color(self, alert_code):
        """Return color based on alert type"""
        colors = {
            'NEW': '#22c55e',   # Green
            'OLD': '#f59e0b',   # Amber
            'LOST': '#ef4444'   # Red
        }
        return colors.get(alert_code, '#64748b')

    def load_logs(self):
        """Load alerts from database and display as cards"""
        try:
            alerts = AlertBusiness.get_recent(limit=200)
            
            # Clear existing cards
            while self.cards_layout.count():
                child = self.cards_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Add new cards
            for alert in alerts:
                card = self.create_alert_card(alert)
                self.cards_layout.addWidget(card)
                
            # Add a placeholder if no alerts
            if not alerts:
                placeholder = QLabel("No alerts to display")
                placeholder.setStyleSheet("color: #64748b; font-size: 16px; padding: 40px;")
                placeholder.setAlignment(Qt.AlignCenter)
                self.cards_layout.addWidget(placeholder)

        except Exception as e:
            print(f"Error loading logs: {e}")

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()