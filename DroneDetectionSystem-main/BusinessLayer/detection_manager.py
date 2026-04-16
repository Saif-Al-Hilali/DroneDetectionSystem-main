# bll/detection_manager.py
from BusinessLayer.track_business import TrackBusiness, TrackMode
from DataAccessLayer.track_repository import TrackDTO

class DetectionManager:

    def process_detection(self, track_uuid, confidence, bbox):
        
        # 1. البحث عن الهدف كـ "كائن حي" (Business Object)
        track_business = TrackBusiness.find(track_uuid)
        
        # 2. إذا لم يكن موجوداً (None)، فهذا هدف جديد
        if track_business is None:
            # نقوم ببناء "كائن هدف جديد" باستخدام البيانات الأولية
            new_dto = TrackDTO(
                track_uuid=track_uuid,
                max_confidence=confidence,
                avg_confidence=confidence,
                is_active=True
            )
            # نضعه في وضع "إضافة" (ADD) ونطلب منه أن يحفظ نفسه في قاعدة البيانات
            track_business = TrackBusiness(new_dto, TrackMode.ADD)
            track_business.save()
            # هنا يمكن إضافة منطق التنبيه (Alert Logic)
            
        # 3. إذا كان موجوداً، فهذا هدف عائد أو مستمر
        else:
            # نقوم بتحديث خصائص الكائن الموجود
            track_business.avg_confidence = confidence
            track_business.max_confidence = max(track_business.max_confidence, confidence)
            track_business.is_active = True
            # نطلب منه أن يحفظ التحديثات (سيقوم تلقائياً بوضع UPDATE)
            track_business.save()