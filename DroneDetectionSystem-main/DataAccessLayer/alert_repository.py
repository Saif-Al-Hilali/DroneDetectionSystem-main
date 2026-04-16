"""
Alert Data - Data Access Layer for alerts table
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.config_manager import config
from typing import List, Optional
from datetime import datetime

class AlertDTO:
    def __init__(self, id: Optional[int] = None, track_id: int = 0,
                 type_id: int = 0, type_code: str = "", type_name: str = "",
                 created_at: Optional[datetime] = None):
        self.id = id
        self.track_id = track_id
        self.type_id = type_id
        self.type_code = type_code
        self.type_name = type_name
        self.created_at = created_at

class AlertData:
    connection_string = config.connection_string

    @staticmethod
    def _get_connection():
        return psycopg2.connect(AlertData.connection_string)

    @staticmethod
    def add_alert(track_id: int, alert_code: str) -> int:
        """Add a new alert"""
        alert_id = 0
        try:
            with AlertData._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT sp_alert_add(%s, %s)", (track_id, alert_code))
                    result = cur.fetchone()
                    if result:
                        alert_id = result[0]
                    conn.commit()
        except Exception as e:
            print(f"Error in add_alert: {e}")
        return alert_id

    @staticmethod
    def get_alerts_by_track(track_id: int) -> List[AlertDTO]:
        """Get all alerts for a specific track"""
        alerts = []
        try:
            with AlertData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_alert_get_by_track(%s)", (track_id,))
                    rows = cur.fetchall()
                    for row in rows:
                        alert = AlertDTO(
                            id=row.get('alert_id'),
                            track_id=track_id,
                            type_code=row.get('alert_code', ''),
                            type_name=row.get('alert_name', ''),
                            created_at=row.get('created_at')
                        )
                        alerts.append(alert)
        except Exception as e:
            print(f"Error in get_alerts_by_track: {e}")
        return alerts

    @staticmethod
    def get_recent_alerts(limit: int = 50) -> List[AlertDTO]:
        """Get recent alerts"""
        alerts = []
        try:
            with AlertData._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sp_alert_get_recent(%s)", (limit,))
                    rows = cur.fetchall()
                    for row in rows:
                        alert = AlertDTO(
                            id=row.get('alert_id'),
                            track_id=0,  # Not returned directly in this SP
                            type_code=row.get('alert_code', ''),
                            type_name=row.get('alert_name', ''),
                            created_at=row.get('created_at')
                        )
                        alerts.append(alert)
        except Exception as e:
            print(f"Error in get_recent_alerts: {e}")
        return alerts