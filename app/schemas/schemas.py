from datetime import datetime
from pydantic import BaseModel


class ScheduleBaseScheme(BaseModel):
    subject: str
    classroom_id: int
    group_id: int
    teacher_id: int
    timestamp_start: datetime
    timestamp_end: datetime

    class Config:
        from_attributes = True


class ScheduleScheme(ScheduleBaseScheme):
    id: int

    class Config:
        from_attributes = True


class ScheduleDaily(ScheduleScheme):
    camera_id: int
    camera_rtsp: str
