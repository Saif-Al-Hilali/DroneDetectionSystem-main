
from typing import Optional, List
from enum import Enum
from DataAccessLayer.track_repository import TrackData, TrackDTO

class TrackMode(Enum):
    ADD = 1
    UPDATE = 0

class TrackBusiness:
    def __init__(self, track_dto: TrackDTO, mode: TrackMode = TrackMode.ADD):
        self.id = track_dto.id
        self.track_uuid = track_dto.track_uuid
        self.first_seen = track_dto.first_seen
        self.last_seen = track_dto.last_seen
        self.total_frames = track_dto.total_frames
        self.max_confidence = track_dto.max_confidence
        self.avg_confidence = track_dto.avg_confidence
        self.is_active = track_dto.is_active
        
        self.mode = mode
        self._repository = TrackData()
    
    @property
    def dto(self) -> TrackDTO:
        return TrackDTO(
            id=self.id,
            track_uuid=self.track_uuid,
            first_seen=self.first_seen,
            last_seen=self.last_seen,
            total_frames=self.total_frames,
            max_confidence=self.max_confidence,
            avg_confidence=self.avg_confidence,
            is_active=self.is_active
        )

    # =====================================================
    # Static Methods (now correctly calling TrackData)
    # =====================================================
    @staticmethod
    def get_all() -> List[TrackDTO]:
        return TrackData.get_all_tracks()

    @staticmethod
    def get_active() -> List[TrackDTO]:
        return TrackData.get_active_tracks()

    @staticmethod
    def find(track_uuid: str) -> Optional['TrackBusiness']:
        track_dto = TrackData.get_track_by_uuid(track_uuid)
        if track_dto:
            return TrackBusiness(track_dto, TrackMode.UPDATE)
        return None

    @staticmethod
    def delete(track_uuid: str) -> bool:
        return TrackData.delete_track(track_uuid)

    @staticmethod
    def mark_inactive(track_uuid: str) -> bool:
        track_id = TrackData.mark_track_inactive(track_uuid)
        return track_id is not None

    # =====================================================
    # Instance Methods
    # =====================================================
    def _add_new(self) -> bool:
        new_id = self._repository.create_track(self.track_uuid, self.max_confidence)
        if new_id:
            self.id = new_id
            return True
        return False

    def _update(self) -> bool:
        updated_id = self._repository.update_track(
            self.track_uuid, self.avg_confidence, self.is_active
        )
        return updated_id > 0

    def save(self) -> bool:
        if self.mode == TrackMode.ADD:
            if self._add_new():
                self.mode = TrackMode.UPDATE
                return True
            return False
        elif self.mode == TrackMode.UPDATE:
            return self._update()
        return False