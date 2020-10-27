from datetime import datetime
from mongoengine import Document
from mongoengine.fields import DateTimeField


class BaseDocument(Document):
    meta = {
        'abstract': True
    }

    date_created = DateTimeField(required=True, default=datetime.utcnow)
    date_updated = DateTimeField(required=True)
    date_deleted = DateTimeField()

    def clean(self):
        super().clean()
        self.date_updated = datetime.utcnow()
