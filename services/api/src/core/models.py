from datetime import datetime
from mongoengine import Document, DateTimeField


class BaseDocument(Document):
    date_created = DateTimeField(required=True)
    date_updated = DateTimeField(required=True)

    meta = {
        'allow_inheritance': True,
        'abstract': True
    }

    def clean(self):
        if self.pk is None:
            self.date_created = datetime.utcnow()
        self.date_updated = datetime.utcnow()

    def to_dict(self):
        return self.to_mongo().to_dict()

