from datetime import datetime
import uuid

from mongoengine import Document
from mongoengine.fields import DateTimeField, UUIDField


class BaseDocument(Document):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
        'strict': False
    }

    uuid = UUIDField(binary=False, required=True, default=uuid.uuid4)
    date_created = DateTimeField(default=datetime.utcnow)
    date_updated = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.date_updated = datetime.utcnow()
        return super().save(*args, **kwargs)
