"""
Detection Service Module
Handles drone detection and tracking using YOLO
"""
import cv2
import cvzone
import torch
from ultralytics import YOLO


class DetectionService:
    """Service class for drone detection and tracking"""

    def __init__(self, model_path, confidence_threshold=0.5):
        """
        Initialize the detection service

        Args:
            model_path: Path to YOLO model file (.pt)
            confidence_threshold: Minimum confidence for detections (0.0 to 1.0)
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.frame_count = 0

        # Determine device (GPU or CPU)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"✅ DetectionService using device: {self.device}")

        if self.device == 'cuda':
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("⚠️ GPU not available, using CPU (will be slower)")

        # Track tracking state
        self.prev_track_ids = set()  # Store previously seen drone IDs
        self.active_tracks = set()  # Store currently active tracks

    def detect(self, frame, use_tracking=True):
        """
        Detect and optionally track drones in a frame

        Args:
            frame: numpy array (BGR image)
            use_tracking: Boolean, whether to use tracking (slower but gives IDs)

        Returns:
            dict with keys:
                - 'boxes': list of (x1, y1, x2, y2) coordinates
                - 'confidences': list of confidence scores
                - 'track_ids': list of track IDs (empty if use_tracking=False)
                - 'is_new': list of boolean (True if new drone)
                - 'colors': list of BGR colors for each detection
        """
        self.frame_count += 1

        # Choose method based on tracking preference
        if use_tracking:
            results = self.model.track(
                frame,
                persist=True,
                conf=self.confidence_threshold,
                iou=0.4,
                tracker='bytetrack.yaml',
                verbose=False,
                imgsz=640 if self.device == 'cuda' else 320,
                device=self.device,
                half=True if self.device == 'cuda' else False
            )
        else:
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=0.4,
                verbose=False,
                imgsz=640 if self.device == 'cuda' else 320,
                device=self.device
            )

        # Parse results
        boxes = []
        confidences = []
        track_ids = []
        is_new = []
        colors = []

        if results and len(results) > 0 and results[0].boxes is not None:
            result_boxes = results[0].boxes
            self.active_tracks.clear()

            for box in result_boxes:
                # Get confidence
                confidence = float(box.conf[0]) if hasattr(box.conf, '__len__') else float(box.conf)

                if confidence < self.confidence_threshold:
                    continue

                # Get coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                boxes.append((x1, y1, x2, y2))
                confidences.append(confidence)

                # Handle tracking IDs
                if use_tracking and box.id is not None:
                    track_id = int(box.id[0]) if hasattr(box.id, '__len__') else int(box.id)
                    track_ids.append(track_id)
                    self.active_tracks.add(str(track_id))

                    # Check if this is a new drone
                    if str(track_id) not in self.prev_track_ids:
                        is_new.append(True)
                        colors.append((0, 0, 255))  # Red for new drone
                        print(f"✅ New drone detected! ID: {track_id}")
                        self.prev_track_ids.add(str(track_id))
                    else:
                        is_new.append(False)
                        colors.append((0, 255, 0))  # Green for stable tracking
                else:
                    track_ids.append(None)
                    is_new.append(False)
                    colors.append((0, 100, 255))  # Orange for no tracking

        return {
            'boxes': boxes,
            'confidences': confidences,
            'track_ids': track_ids,
            'is_new': is_new,
            'colors': colors,
            'active_count': len(self.active_tracks)
        }


    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame

        Args:
            frame: numpy array (BGR image)
            detections: dict from detect() method

        Returns:
            frame with drawings
        """
        for i in range(len(detections['boxes'])):
            x1, y1, x2, y2 = detections['boxes'][i]
            confidence = detections['confidences'][i]
            track_id = detections['track_ids'][i]
            color = detections['colors'][i]

            # Calculate width and height
            w, h = x2 - x1, y2 - y1

            # Draw corner rectangle
            cvzone.cornerRect(frame, [x1, y1, w, h], colorR=color, l=10, t=2)

            # Draw rectangle (alternative)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Create label text
            if track_id is not None:
                label = f"Drone {track_id} ({confidence:.2f})"
            else:
                label = f"Drone ({confidence:.2f})"

            # Draw text with background
            cvzone.putTextRect(
                frame,
                label,
                (x1, y1 - 10),
                scale=0.7,
                thickness=2,
                colorR=color,
                colorT=(255, 255, 255)  # White text
            )

        return frame

    def get_stats(self):
        """Get detection statistics"""
        return {
            'total_frames': self.frame_count,
            'unique_drones': len(self.prev_track_ids),
            'active_drones': len(self.active_tracks),
            'device': self.device
        }

    def reset_tracking(self):
        """Reset tracking history (for new video/file)"""
        self.prev_track_ids.clear()
        self.active_tracks.clear()
        print("🔄 Tracking history reset")