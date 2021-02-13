from datetime import datetime
import uuid 
from mongoengine import Document
from mongoengine.fields import DateTimeField, UUIDField


class BaseDocument(Document):
    meta = {
        'abstract': True
    }

    uuid = UUIDField(required=True, unique=True, default=uuid.uuid4)
    date_created = DateTimeField(default=datetime.utcnow)
    date_updated = DateTimeField()
    date_deleted = DateTimeField()

    def clean(self):
        super().clean()
        not_saved = self.pk is None
        changed_fields = self._get_changed_fields()
        if not_saved or changed_fields:
            self.date_updated = datetime.utcnow()

    def soft_delete(self):
        self.date_deleted = datetime.utcnow()
        self.save()
