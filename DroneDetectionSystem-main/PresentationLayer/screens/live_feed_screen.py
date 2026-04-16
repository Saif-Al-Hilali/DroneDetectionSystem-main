import cv2
import cvzone
import os
import torch
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                             QPushButton, QComboBox, QFileDialog, QMessageBox,
                             QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, QMutex, QWaitCondition
from PyQt5.QtGui import QImage, QPixmap
from ultralytics import YOLO

from BusinessLayer.detection_manager import DetectionManager
from scripts.config_manager import config


class VideoCaptureThread(QThread):
    """
    Thread dedicated to capturing frames from camera/video file.
    Emits only the latest frame (no queue explosion).
    """
    new_frame = pyqtSignal(object)  # numpy array (frame)

    def __init__(self, source):
        super().__init__()
        self.source = source
        self._is_running = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.target_size = (640, 640)  # resize once here

    def set_target_size(self, width, height):
        self.target_size = (width, height)

    def run(self):
        self.mutex.lock()
        self._is_running = True
        self.mutex.unlock()

        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            self.new_frame.emit(None)  # error signal
            return

        # Get FPS for proper delay
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        delay_ms = int(1000 / fps)

        frame_counter = 0
        while True:
            self.mutex.lock()
            running = self._is_running
            self.mutex.unlock()
            if not running:
                break

            ret, frame = cap.read()
            if not ret:
                break

            # Resize immediately to reduce inference load
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
            frame_counter += 1

            # Emit only the latest frame (old frames are discarded)
            self.new_frame.emit(frame)

            # Control frame rate for file source
            if isinstance(self.source, str):
                self.msleep(delay_ms)
            else:
                self.msleep(10)  # webcam ~100 fps max

        cap.release()
        self.new_frame.emit(None)  # signal end of stream

    def stop(self):
        self.mutex.lock()
        self._is_running = False
        self.cond.wakeAll()
        self.mutex.unlock()
        self.wait()


class InferenceThread(QThread):
    """
    Separate thread for YOLO inference on GPU.
    Uses latest frame only (frame buffer behaviour).
    """
    result_ready = pyqtSignal(object, object, dict)  # original frame, annotated frame, stats

    def __init__(self, model, confidence_threshold):
        super().__init__()
        self.model = model
        self.conf = confidence_threshold
        self.frame = None
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.running = True

        # Tracking statistics
        self.prev_track_ids = set()
        self.active_tracks = set()
        self.frame_count = 0
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def submit_frame(self, frame):
        """Submit the latest frame for inference (overwrites previous pending)."""
        self.mutex.lock()
        self.frame = frame.copy() if frame is not None else None
        self.cond.wakeOne()
        self.mutex.unlock()

    def run(self):
        while self.running:
            self.mutex.lock()
            if self.frame is None:
                self.cond.wait(self.mutex)
            frame = self.frame
            self.frame = None  # consume, keep only latest
            self.mutex.unlock()

            if frame is not None and self.running:
                self.frame_count += 1

                # GPU inference with no gradient overhead
                with torch.no_grad():
                    results = self.model.track(
                        frame,
                        persist=True,
                        conf=self.conf,
                        iou=0.4,
                        tracker='bytetrack.yaml',
                        verbose=False,
                        imgsz=frame.shape[1],  # already resized
                        device=self.device
                    )

                # Extract statistics
                stats = self.extract_statistics(results)

                # Draw results on a copy
                annotated = self.draw_detections(frame.copy(), results)
                self.result_ready.emit(frame, annotated, stats)

    def extract_statistics(self, results):
        """Extract detection statistics from results"""
        stats = {
            'frame_number': self.frame_count,
            'device': self.device.upper(),
            'total_detections': 0,
            'tracked_drones': 0,
            'untracked_drones': 0,
            'unique_drones': len(self.prev_track_ids),
            'active_tracks': 0,
            'new_drones': [],
            'detections': []
        }

        if results[0].boxes is None:
            return stats

        boxes = results[0].boxes
        stats['total_detections'] = len(boxes)
        self.active_tracks.clear()

        for box in boxes:
            conf = float(box.conf[0]) if hasattr(box.conf, '__len__') else float(box.conf)
            if conf < self.conf:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            if box.id is not None:
                track_id = int(box.id[0]) if hasattr(box.id, '__len__') else int(box.id)
                self.active_tracks.add(str(track_id))
                stats['tracked_drones'] += 1

                # Check if new drone
                if str(track_id) not in self.prev_track_ids:
                    stats['new_drones'].append(track_id)
                    self.prev_track_ids.add(str(track_id))

                stats['detections'].append({
                    'type': 'tracked',
                    'id': track_id,
                    'confidence': conf,
                    'bbox': (x1, y1, x2, y2)
                })
            else:
                stats['untracked_drones'] += 1
                stats['detections'].append({
                    'type': 'untracked',
                    'confidence': conf,
                    'bbox': (x1, y1, x2, y2)
                })

        stats['active_tracks'] = len(self.active_tracks)
        return stats

    def draw_detections(self, frame, results):
        """Draw bounding boxes and labels (lightweight, runs in inference thread)."""
        if results[0].boxes is None:
            return frame

        boxes = results[0].boxes
        for box in boxes:
            conf = float(box.conf[0]) if hasattr(box.conf, '__len__') else float(box.conf)
            if conf < self.conf:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            w, h = x2 - x1, y2 - y1

            if box.id is not None:
                track_id = int(box.id[0]) if hasattr(box.id, '__len__') else int(box.id)
                # Check if new drone (within last 5 frames for visual indication)
                if str(track_id) in self.prev_track_ids:
                    color = (0, 255, 0)  # Green for existing tracked
                else:
                    color = (0, 0, 255)  # Red for new drone
                label = f"Drone {track_id} ({conf:.2f})"
            else:
                color = (0, 100, 255)  # Orange for untracked
                label = f"Drone ({conf:.2f})"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cvzone.cornerRect(frame, [x1, y1, w, h], colorR=color, l=10, t=2)
            cvzone.putTextRect(frame, label, (x1, y1 - 10),
                               scale=0.7, thickness=2, colorR=color, colorT=(255, 255, 255))
        return frame

    def stop(self):
        self.running = False
        self.cond.wakeOne()
        self.wait()

    def reset_tracking(self):
        """Reset tracking history for new video"""
        self.prev_track_ids.clear()
        self.active_tracks.clear()
        self.frame_count = 0
        print("🔄 Tracking history reset")


class LiveFeedScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("liveFeed")

        # GPU info
        print(f"🔍 CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ GPU not available, using CPU")

        # Load model (once, will be used in inference thread)
        self.model = YOLO(config.model_path)
        self.detection_manager = DetectionManager()
        self.confidence_threshold = config.confidence_threshold

        # Threads
        self.capture_thread = None
        self.inference_thread = None

        self.current_source_type = "webcam"
        self.current_file_path = ""

        self.setup_ui()

        # Start inference thread immediately
        self.inference_thread = InferenceThread(self.model, self.confidence_threshold)
        self.inference_thread.result_ready.connect(self.display_frame)
        self.inference_thread.start()

    def setup_ui(self):
        """Setup UI with enhanced statistics display"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title
        title = QLabel("Live Feed - Drone Surveillance")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#38bdf8;")
        main_layout.addWidget(title)

        # Control panel
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        control_layout.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItem("Live Webcam", "webcam")
        self.source_combo.addItem("Video File", "file")
        self.source_combo.setStyleSheet("padding:6px; border-radius:5px; background:#1e293b; color:white;")
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        control_layout.addWidget(self.source_combo)

        self.file_path_label = QLabel("Using default webcam")
        self.file_path_label.setStyleSheet("color:#94a3b8; font-size:12px;")
        self.file_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        control_layout.addWidget(self.file_path_label)

        control_layout.addStretch()

        # Buttons
        self.start_btn = QPushButton("Start Stream")
        self.start_btn.setStyleSheet(
            "QPushButton { background:#22c55e; color:white; border-radius:5px; padding:6px 20px; font-weight:bold; } QPushButton:hover { background:#16a34a; }")
        self.start_btn.clicked.connect(self.start_stream)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Stream")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            "QPushButton { background:#ef4444; color:white; border-radius:5px; padding:6px 20px; font-weight:bold; } QPushButton:hover { background:#dc2626; } QPushButton:disabled { background:#475569; }")
        self.stop_btn.clicked.connect(self.stop_stream)
        control_layout.addWidget(self.stop_btn)

        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setStyleSheet(
            "QPushButton { background:#3b82f6; color:white; border-radius:5px; padding:6px 15px; } QPushButton:hover { background:#2563eb; }")
        self.upload_btn.clicked.connect(self.choose_file)
        control_layout.addWidget(self.upload_btn)
        self.upload_btn.hide()

        main_layout.addWidget(control_widget)

        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:black; border-radius:10px; border:1px solid #334155;")
        self.video_label.setText("Stream stopped")
        self.video_label.setScaledContents(False)
        main_layout.addWidget(self.video_label, 1)

        # ========== ENHANCED STATUS BAR ==========
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        # Status indicator
        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("color:#f59e0b; font-size:14px;font-weight:bold;")
        status_layout.addWidget(self.status_label)

        # Separator
        separator1 = QLabel("|")
        separator1.setStyleSheet("color:#334155; font-size:14px;")
        status_layout.addWidget(separator1)

        # Frame counter
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setStyleSheet("color:#94a3b8; font-size:12px;")
        status_layout.addWidget(self.frame_label)

        # Separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("color:#334155; font-size:14px;")
        status_layout.addWidget(separator2)

        # Active targets
        self.stats_label = QLabel("Active: 0")
        self.stats_label.setStyleSheet("color:#22c55e; font-size:12px;font-weight:bold;")
        status_layout.addWidget(self.stats_label)

        # Separator
        separator3 = QLabel("|")
        separator3.setStyleSheet("color:#334155; font-size:14px;")
        status_layout.addWidget(separator3)

        # Total unique drones
        self.unique_label = QLabel("Total: 0")
        self.unique_label.setStyleSheet("color:#38bdf8; font-size:12px;font-weight:bold;")
        status_layout.addWidget(self.unique_label)

        # Separator
        separator4 = QLabel("|")
        separator4.setStyleSheet("color:#334155; font-size:14px;")
        status_layout.addWidget(separator4)

        # Device info
        device_text = "GPU" if torch.cuda.is_available() else "CPU"
        device_color = "#22c55e" if torch.cuda.is_available() else "#f59e0b"
        self.device_label = QLabel(f"Device: {device_text}")
        self.device_label.setStyleSheet(f"color:{device_color}; font-size:12px;font-weight:bold;")
        status_layout.addWidget(self.device_label)

        # Separator
        separator5 = QLabel("|")
        separator5.setStyleSheet("color:#334155; font-size:14px;")
        status_layout.addWidget(separator5)

        # Tracking status
        self.tracking_status = QLabel("Tracking: ON")
        self.tracking_status.setStyleSheet("color:#8b5cf6; font-size:12px;font-weight:bold;")
        status_layout.addWidget(self.tracking_status)

        status_layout.addStretch()
        main_layout.addWidget(status_widget)

        # ========== SECONDARY INFO BAR (Detections) ==========
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Detection summary
        self.detection_summary = QLabel("📡 Waiting for stream...")
        self.detection_summary.setStyleSheet("color:#64748b; font-size:11px;")
        info_layout.addWidget(self.detection_summary)

        info_layout.addStretch()

        # New drone alert
        self.new_drone_alert = QLabel("")
        self.new_drone_alert.setStyleSheet("color:#ef4444; font-size:11px;font-weight:bold;")
        info_layout.addWidget(self.new_drone_alert)

        main_layout.addWidget(info_widget)
        # ====================================================

    def get_target_size(self):
        if self.isFullScreen():
            return 640, 640
        else:
            return 480, 480

    def on_source_changed(self, index):
        source_type = self.source_combo.currentData()
        self.current_source_type = source_type
        if source_type == "webcam":
            self.upload_btn.hide()
            self.file_path_label.setText("Using default webcam")
        else:
            self.upload_btn.show()
            self.file_path_label.setText("No file selected")

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            # Reset tracking when new file is loaded
            if self.inference_thread:
                self.inference_thread.reset_tracking()

    def start_stream(self):
        if self.current_source_type == "webcam":
            source = 0
        else:
            if not self.current_file_path:
                QMessageBox.warning(self, "No File", "Please select a video file first.")
                return
            source = self.current_file_path
            # Reset tracking for new video
            if self.inference_thread:
                self.inference_thread.reset_tracking()

        # Stop any existing capture thread
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread = None

        # Create and start capture thread
        self.capture_thread = VideoCaptureThread(source)
        w, h = self.get_target_size()
        self.capture_thread.set_target_size(w, h)
        self.capture_thread.new_frame.connect(self.on_new_frame)
        self.capture_thread.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.source_combo.setEnabled(False)
        self.status_label.setText("Status: Streaming")
        self.status_label.setStyleSheet("color:#22c55e; font-size:14px;font-weight:bold;")
        self.detection_summary.setText("📡 Detecting drones...")

    def on_new_frame(self, frame):
        """Called from capture thread with latest frame. Forward to inference thread."""
        if frame is None:
            # End of stream
            self.stop_stream()
            return
        if self.inference_thread:
            self.inference_thread.submit_frame(frame)

    def display_frame(self, original_frame, annotated_frame, stats):
        """Called from inference thread with result. Update UI with statistics."""
        # Update statistics labels
        self.frame_label.setText(f"Frame: {stats['frame_number']}")
        self.stats_label.setText(f"Active: {stats['active_tracks']}")
        self.unique_label.setText(f"Total: {stats['unique_drones']}")

        # Update detection summary
        if stats['total_detections'] > 0:
            summary_parts = []
            if stats['tracked_drones'] > 0:
                summary_parts.append(f"🎯 Tracked: {stats['tracked_drones']}")
            if stats['untracked_drones'] > 0:
                summary_parts.append(f"⚠️ Untracked: {stats['untracked_drones']}")
            self.detection_summary.setText(" | ".join(summary_parts))
            self.detection_summary.setStyleSheet("color:#22c55e; font-size:11px;")
        else:
            self.detection_summary.setText("🔍 No drones detected")
            self.detection_summary.setStyleSheet("color:#64748b; font-size:11px;")

        # Show new drone alerts
        if stats['new_drones']:
            new_ids = ", ".join([str(i) for i in stats['new_drones']])
            self.new_drone_alert.setText(f"🚨 NEW DRONE(S) DETECTED! ID: {new_ids}")
            self.new_drone_alert.setStyleSheet("color:#ef4444; font-size:11px;font-weight:bold;")
            # Auto-clear alert after 2 seconds
            QTimer.singleShot(2000, lambda: self.new_drone_alert.setText(""))
        else:
            # Don't clear immediately, only if no new drones for a while
            pass

        # Display the annotated frame
        rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap)
        self.video_label.setFixedSize(w, h)

        # Also print to console (optional)
        print(f"\n[Frame {stats['frame_number']}] "
              f"Device: {stats['device']}, "
              f"Tracked: {stats['tracked_drones']}, "
              f"Untracked: {stats['untracked_drones']}, "
              f"Active: {stats['active_tracks']}, "
              f"Total Unique: {stats['unique_drones']}")

    def stop_stream(self):
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.source_combo.setEnabled(True)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color:#f59e0b; font-size:14px;font-weight:bold;")
        self.video_label.setText("Stream stopped")
        self.stats_label.setText("Active: 0")
        self.frame_label.setText("Frame: 0")
        self.unique_label.setText("Total: 0")
        self.detection_summary.setText("📡 Waiting for stream...")
        self.new_drone_alert.setText("")

    def closeEvent(self, event):
        if self.capture_thread:
            self.capture_thread.stop()
        if self.inference_thread:
            self.inference_thread.stop()
        event.accept()