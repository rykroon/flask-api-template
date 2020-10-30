from datetime import datetime
import uuid 
from mongoengine import Document
from mongoengine.fields import DateTimeField, UUIDField


class BaseDocument(Document):
    meta = {
        'abstract': True
    }

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    date_created = DateTimeField(required=True, default=datetime.utcnow)
    date_updated = DateTimeField()
    date_deleted = DateTimeField()

    def clean(self):
        super().clean()
        if self.pk is not None:
            self.date_updated = datetime.utcnow()

    def soft_delete(self):
        self.date_deleted = datetime.utcnow()
        self.save()
