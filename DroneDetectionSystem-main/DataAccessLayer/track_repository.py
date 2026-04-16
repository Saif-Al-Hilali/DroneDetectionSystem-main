"""
Track Data - Data Access Layer for tracks table
Similar to StudentData class in your example
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.config_manager import config
from typing import List, Optional
from datetime import datetime

# =====================================================
# Track DTO
# =====================================================
class TrackDTO:
    def __init__(self, id: Optional[int] = None, track_uuid: str = "",
                 first_seen: Optional[datetime] = None, last_seen: Optional[datetime] = None,
                 total_frames: int = 0, max_confidence: float = 0.0,
                 avg_confidence: float = 0.0, is_active: bool = True):
        self.id = id
        self.track_uuid = track_uuid
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.total_frames = total_frames
        self.max_confidence = max_confidence
        self.avg_confidence = avg_confidence
        self.is_active = is_active

# =====================================================
# Track Data (Static Methods like your StudentData)
# =====================================================
class TrackData:
    connection_string = config.connection_string

    @staticmethod
    def _get_connection():
        return psycopg2.connect(TrackData.connection_string)

    @staticmethod
    def get_all_tracks() -> List[TrackDTO]:
        """Get all tracks (similar to GetAllStudents)"""
        tracks = []
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_track_get_recent(%s)", (1000,))
                    rows = cur.fetchall()
                    for row in rows:
                        track = TrackDTO(
                            id=row.get('id'),
                            track_uuid=row.get('track_uuid', ''),
                            first_seen=row.get('first_seen'),
                            last_seen=row.get('last_seen'),
                            total_frames=row.get('total_frames', 0),
                            max_confidence=float(row.get('max_confidence', 0.0) or 0.0),
                            avg_confidence=float(row.get('avg_confidence', 0.0) or 0.0),
                            is_active=row.get('is_active', True)
                        )
                        tracks.append(track)
        except Exception as e:
            print(f"Error in get_all_tracks: {e}")
        return tracks

    @staticmethod
    def get_active_tracks() -> List[TrackDTO]:
        """Get only active tracks"""
        tracks = []
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_track_get_active()")
                    rows = cur.fetchall()
                    for row in rows:
                        track = TrackDTO(
                            id=row.get('id'),
                            track_uuid=row.get('track_uuid', ''),
                            first_seen=row.get('first_seen'),
                            last_seen=row.get('last_seen'),
                            total_frames=row.get('total_frames', 0),
                            max_confidence=float(row.get('max_confidence', 0.0) or 0.0),
                            avg_confidence=float(row.get('avg_confidence', 0.0) or 0.0),
                            is_active=row.get('is_active', True)
                        )
                        tracks.append(track)
        except Exception as e:
            print(f"Error in get_active_tracks: {e}")
        return tracks

    @staticmethod
    def get_track_by_uuid(track_uuid: str) -> Optional[TrackDTO]:
        """Get track by UUID (similar to GetStudentByID)"""
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_track_get_by_uuid(%s)", (track_uuid,))
                    row = cur.fetchone()
                    if row:
                        return TrackDTO(
                            id=row.get('id'),
                            track_uuid=row.get('track_uuid', ''),
                            first_seen=row.get('first_seen'),
                            last_seen=row.get('last_seen'),
                            total_frames=row.get('total_frames', 0),
                            max_confidence=float(row.get('max_confidence', 0.0) or 0.0),
                            avg_confidence=float(row.get('avg_confidence', 0.0) or 0.0),
                            is_active=row.get('is_active', True)
                        )
        except Exception as e:
            print(f"Error in get_track_by_uuid: {e}")
        return None

    @staticmethod
    def check_track(track_uuid: str) -> dict:
        """Check if track exists and its status"""
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM sp_track_check(%s)", (track_uuid,))
                    row = cur.fetchone()
                    if row:
                        return {
                            'track_id': row[0],
                            'track_exists': row[1],
                            'is_active': row[2]
                        }
        except Exception as e:
            print(f"Error in check_track: {e}")
        return {'track_id': None, 'track_exists': False, 'is_active': False}

    @staticmethod
    def create_track(track_uuid: str, confidence: float) -> int:
        """Create new track (similar to AddNewStudent)"""
        new_id = 0
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_track_create(%s, %s)", (track_uuid, confidence))
                    result = cur.fetchone()
                    if result:
                        new_id = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in create_track: {e}")
        return new_id

    @staticmethod
    def update_track(track_uuid: str, confidence: float, is_active: bool = True) -> int:
        """Update existing track (similar to UpdateStudent)"""
        track_id = 0
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_track_update(%s, %s, %s)", (track_uuid, confidence, is_active))
                    result = cur.fetchone()
                    if result:
                        track_id = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in update_track: {e}")
        return track_id

    @staticmethod
    def mark_track_inactive(track_uuid: str) -> Optional[int]:
        """Mark track as lost"""
        track_id = None
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_track_mark_inactive(%s)", (track_uuid,))
                    result = cur.fetchone()
                    if result:
                        track_id = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in mark_track_inactive: {e}")
        return track_id

    @staticmethod
    def delete_track(track_uuid: str) -> bool:
        """Delete track (similar to DeleteStudent)"""
        affected = 0
        try:
            with TrackData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_track_delete(%s)", (track_uuid,))
                    result = cur.fetchone()
                    if result:
                        affected = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in delete_track: {e}")
        return affected > 0