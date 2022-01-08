from datetime import datetime

from mongoengine import Document
from mongoengine.fields import DateTimeField, UUIDField

class BaseDocument(Document):

    uuid = UUIDField()
    date_created = DateTimeField()
    date_updated = DateTimeField()
