
from typing import Optional, List
from enum import Enum
from DataAccessLayer.alert_repository import AlertData, AlertDTO

class AlertMode(Enum):
    ADD = 1
    UPDATE = 0

class AlertBusiness:
    def __init__(self, alert_dto: AlertDTO, mode: AlertMode = AlertMode.ADD):
        self.id = alert_dto.id
        self.track_id = alert_dto.track_id
        self.type_id = alert_dto.type_id
        self.type_code = alert_dto.type_code
        self.type_name = alert_dto.type_name
        self.created_at = alert_dto.created_at
        
        self.mode = mode
        self._repository = AlertData()
    
    @property
    def dto(self) -> AlertDTO:
        return AlertDTO(
            id=self.id,
            track_id=self.track_id,
            type_id=self.type_id,
            type_code=self.type_code,
            type_name=self.type_name,
            created_at=self.created_at
        )

    @staticmethod
    def get_recent(limit: int = 50) -> List[AlertDTO]:
        return AlertData.get_recent_alerts(limit)

    @staticmethod
    def get_by_track(track_id: int) -> List[AlertDTO]:
        return AlertData.get_alerts_by_track(track_id)

    def _add_new(self) -> bool:
        new_id = self._repository.add_alert(self.track_id, self.type_code)
        if new_id:
            self.id = new_id
            return True
        return False

    def save(self) -> bool:
        if self.mode == AlertMode.ADD:
            return self._add_new()
        return False