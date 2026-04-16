"""
TrackPoint Business Layer
"""
from typing import List, Optional
from DataAccessLayer.track_point_repository import TrackPointData
from DataAccessLayer.track_point_repository import TrackPointDTO

class TrackPointBusiness:
    def __init__(self, point_dto: TrackPointDTO):
        self.id = point_dto.id
        self.track_id = point_dto.track_id
        self.bbox_x1 = point_dto.bbox_x1
        self.bbox_y1 = point_dto.bbox_y1
        self.bbox_x2 = point_dto.bbox_x2
        self.bbox_y2 = point_dto.bbox_y2
        self.confidence = point_dto.confidence
        self.point_time = point_dto.point_time
        
        self._repository = TrackPointData()
    
    @staticmethod
    def get_by_track(track_id: int, limit: int = 1000) -> List[TrackPointDTO]:
        repo = TrackPointData()
        return repo.get_by_track(track_id, limit)
    
    def save(self) -> bool:
        """Add a new track point"""
        new_id = self._repository.add(
            track_id=self.track_id,
            x1=self.bbox_x1,
            y1=self.bbox_y1,
            x2=self.bbox_x2,
            y2=self.bbox_y2,
            confidence=self.confidence
        )
        if new_id:
            self.id = new_id
            return True
        return False