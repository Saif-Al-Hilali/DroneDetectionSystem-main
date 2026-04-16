"""
Track Point Data - Data Access Layer for track_points table
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.config_manager import config
from typing import List, Optional
from datetime import datetime

class TrackPointDTO:
    def __init__(self, id: Optional[int] = None, track_id: int = 0,
                 bbox_x1: int = 0, bbox_y1: int = 0, bbox_x2: int = 0, bbox_y2: int = 0,
                 confidence: float = 0.0, point_time: Optional[datetime] = None):
        self.id = id
        self.track_id = track_id
        self.bbox_x1 = bbox_x1
        self.bbox_y1 = bbox_y1
        self.bbox_x2 = bbox_x2
        self.bbox_y2 = bbox_y2
        self.confidence = confidence
        self.point_time = point_time

class TrackPointData:
    connection_string = config.connection_string

    @staticmethod
    def _get_connection():
        return psycopg2.connect(TrackPointData.connection_string)

    @staticmethod
    def add_track_point(track_id: int, x1: int, y1: int, x2: int, y2: int, confidence: float) -> int:
        """Add a track point"""
        point_id = 0
        try:
            with TrackPointData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_track_point_add(%s, %s, %s, %s, %s, %s)",
                               (track_id, x1, y1, x2, y2, confidence))
                    result = cur.fetchone()
                    if result:
                        point_id = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in add_track_point: {e}")
        return point_id

    @staticmethod
    def get_points_by_track(track_id: int, limit: int = 1000) -> List[TrackPointDTO]:
        """Get all points for a track"""
        points = []
        try:
            with TrackPointData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_track_point_get_by_track(%s, %s)", (track_id, limit))
                    rows = cur.fetchall()
                    for row in rows:
                        point = TrackPointDTO(
                            id=row.get('id'),
                            track_id=row.get('track_id', 0),
                            bbox_x1=row.get('bbox_x1', 0),
                            bbox_y1=row.get('bbox_y1', 0),
                            bbox_x2=row.get('bbox_x2', 0),
                            bbox_y2=row.get('bbox_y2', 0),
                            confidence=float(row.get('confidence', 0.0) or 0.0),
                            point_time=row.get('point_time')
                        )
                        points.append(point)
        except Exception as e:
            print(f"Error in get_points_by_track: {e}")
        return points