"""
Detection Data - Composite operations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.config_manager import config
from typing import Optional

class DetectionResultDTO:
    def __init__(self, track_id: Optional[int] = None, is_new: bool = False,
                 was_inactive: bool = False, alert_added: bool = False,
                 alert_code: Optional[str] = None):
        self.track_id = track_id
        self.is_new = is_new
        self.was_inactive = was_inactive
        self.alert_added = alert_added
        self.alert_code = alert_code

class DetectionData:
    connection_string = config.connection_string

    @staticmethod
    def _get_connection():
        return psycopg2.connect(DetectionData.connection_string)

    @staticmethod
    def process_detection(track_uuid: str, confidence: float,
                          x1: int, y1: int, x2: int, y2: int) -> DetectionResultDTO:
        """Process a single detection (composite operation)"""
        try:
            with DetectionData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_process_detection(%s, %s, %s, %s, %s, %s)",
                               (track_uuid, confidence, x1, y1, x2, y2))
                    row = cur.fetchone()
                    conn.commit()
                    if row:
                        return DetectionResultDTO(
                            track_id=row.get('track_id'),
                            is_new=row.get('is_new', False),
                            was_inactive=row.get('was_inactive', False),
                            alert_added=row.get('alert_added', False),
                            alert_code=row.get('alert_code')
                        )
        except Exception as e:
            print(f"Error in process_detection: {e}")
        return DetectionResultDTO()

    @staticmethod
    def process_lost(track_uuid: str) -> dict:
        """Process a lost target"""
        try:
            with DetectionData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_process_lost(%s)", (track_uuid,))
                    row = cur.fetchone()
                    conn.commit()
                    if row:
                        return {
                            'track_id': row.get('track_id'),
                            'was_updated': row.get('was_updated', False),
                            'alert_added': row.get('alert_added', False)
                        }
        except Exception as e:
            print(f"Error in process_lost: {e}")
        return {'track_id': None, 'was_updated': False, 'alert_added': False}