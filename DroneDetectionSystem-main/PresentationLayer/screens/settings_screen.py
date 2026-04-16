from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
                             QMessageBox, QTabWidget, QFormLayout, QSizePolicy)
from PyQt5.QtCore import Qt
import json
import os
import psycopg2


class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("settingsScreen")
        self.config_file = "config.json"
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(25)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #38bdf8;")
        title.setAlignment(Qt.AlignLeft)

        header_layout.addWidget(title)
        main_layout.addLayout(header_layout)

        # Tab widget with dark theme adaptation
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 12px;
                background: transparent;
                padding: 20px;
            }
            QTabBar::tab {
                background: transparent;
                color: #94a3b8;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 500;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border-bottom: 3px solid #38bdf8;
            }
            QTabBar::tab:hover:!selected {
                background: #1e293b;
                color: #f1f5f9;
            }
        """)

        # Create tabs
        self.camera_tab = self.create_camera_tab()
        self.model_tab = self.create_model_tab()
        self.database_tab = self.create_database_tab()

        self.tab_widget.addTab(self.camera_tab, "Camera")
        self.tab_widget.addTab(self.model_tab, "Model")
        self.tab_widget.addTab(self.database_tab, "Database")

        main_layout.addWidget(self.tab_widget)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1e293b;
                border-color: #64748b;
                color: #f1f5f9;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #38bdf8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0ea5e9;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        # Global widget style (dark theme base)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QLabel {
                color: #94a3b8;
                font-size: 14px;
            }
            /* Light input fields for contrast */
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 10px 14px;
                color: #1e293b;
                font-size: 14px;
                selection-background-color: #bfdbfe;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #38bdf8;
                background: white;
            }
            QLineEdit:disabled {
                background: #334155;
                color: #64748b;
            }
        """)

    def create_camera_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        desc = QLabel("Configure the video source for live feed processing.")
        desc.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(desc)

        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.camera_source = QLineEdit()
        self.camera_source.setPlaceholderText("0 (default webcam) or RTSP URL")
        self.camera_source.setClearButtonEnabled(True)
        self.camera_source.setMinimumWidth(400)
        form_layout.addRow("Video Source:", self.camera_source)

        layout.addLayout(form_layout)
        layout.addStretch()
        return tab

    def create_model_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        desc = QLabel("Configure the YOLO model and detection parameters.")
        desc.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(desc)

        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("models/yolo11l.pt")
        self.model_path.setClearButtonEnabled(True)
        form_layout.addRow("Model Path:", self.model_path)

        self.confidence_threshold = QDoubleSpinBox()
        self.confidence_threshold.setRange(0.1, 1.0)
        self.confidence_threshold.setSingleStep(0.05)
        self.confidence_threshold.setValue(0.5)
        self.confidence_threshold.setSuffix(" (0.1 - 1.0)")
        form_layout.addRow("Confidence Threshold:", self.confidence_threshold)

        layout.addLayout(form_layout)
        layout.addStretch()
        return tab

    def create_database_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        desc = QLabel("PostgreSQL connection settings for data storage.")
        desc.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(desc)

        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.db_host = QLineEdit()
        self.db_host.setPlaceholderText("localhost")
        self.db_host.setClearButtonEnabled(True)
        form_layout.addRow("Host:", self.db_host)

        self.db_port = QSpinBox()
        self.db_port.setRange(1, 65535)
        self.db_port.setValue(5432)
        form_layout.addRow("Port:", self.db_port)

        self.db_name = QLineEdit()
        self.db_name.setPlaceholderText("drone_detection")
        self.db_name.setClearButtonEnabled(True)
        form_layout.addRow("Database Name:", self.db_name)

        self.db_user = QLineEdit()
        self.db_user.setPlaceholderText("postgres")
        self.db_user.setClearButtonEnabled(True)
        form_layout.addRow("Username:", self.db_user)

        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.Password)
        self.db_password.setPlaceholderText("••••••••")
        self.db_password.setClearButtonEnabled(True)
        form_layout.addRow("Password:", self.db_password)

        layout.addLayout(form_layout)

        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #38bdf8;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.1);
            }
        """)
        self.test_btn.clicked.connect(self.test_db_connection)
        test_btn_layout.addWidget(self.test_btn)
        layout.addLayout(test_btn_layout)

        layout.addStretch()
        return tab

    def test_db_connection(self):
        try:
            conn = psycopg2.connect(
                host=self.db_host.text() or "localhost",
                port=self.db_port.value(),
                dbname=self.db_name.text() or "drone_detection",
                user=self.db_user.text() or "postgres",
                password=self.db_password.text(),
                connect_timeout=5
            )
            conn.close()
            QMessageBox.information(self, "Connection Test", "✓ Database connection successful!")
        except Exception as e:
            QMessageBox.critical(self, "Connection Test", f"✗ Connection failed:\n{str(e)}")

    def load_settings(self):
        defaults = {
            "camera_source": "0",
            "model_path": "yolo11l.pt",
            "confidence_threshold": 0.5,
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "drone_detection",
            "db_user": "postgres",
            "db_password": ""
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    defaults.update(settings)
            except Exception:
                pass

        self.camera_source.setText(str(defaults.get("camera_source", "0")))
        self.model_path.setText(defaults.get("model_path", "yolo11l.pt"))
        self.confidence_threshold.setValue(defaults.get("confidence_threshold", 0.5))
        self.db_host.setText(defaults.get("db_host", "localhost"))
        self.db_port.setValue(defaults.get("db_port", 5432))
        self.db_name.setText(defaults.get("db_name", "drone_detection"))
        self.db_user.setText(defaults.get("db_user", "postgres"))
        self.db_password.setText(defaults.get("db_password", ""))

    def save_settings(self):
        settings = {
            "camera_source": self.camera_source.text(),
            "model_path": self.model_path.text(),
            "confidence_threshold": self.confidence_threshold.value(),
            "db_host": self.db_host.text(),
            "db_port": self.db_port.value(),
            "db_name": self.db_name.text(),
            "db_user": self.db_user.text(),
            "db_password": self.db_password.text()
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=4)
            QMessageBox.information(self, "Settings Saved",
                                    "Configuration saved successfully.\nRestart the application to apply changes.")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Could not save settings:\n{str(e)}")

    def reset_defaults(self):
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Restore all settings to their default values?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.camera_source.setText("0")
            self.model_path.setText("yolo11l.pt")
            self.confidence_threshold.setValue(0.5)
            self.db_host.setText("localhost")
            self.db_port.setValue(5432)
            self.db_name.setText("drone_detection")
            self.db_user.setText("postgres")
            self.db_password.setText("")