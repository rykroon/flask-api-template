from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from mongomini import Document


class BaseSchema(BaseModel):
    _id: Optional[ObjectId]
    date_created: datetime = Field(datetime.utcnow)
    date_updated: datetime = Field(datetime.utcnow)
    date_deleted: Optional[datetime]

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())


class BaseDocument(Document):
    class Config:
        abstract = True