from secrets import token_urlsafe
from typing import Optional

from flask import current_app
from pydantic import Field, HttpUrl

from mongomini import Document

from .base import BaseDocument, BaseSchema


class ClientSchema(BaseSchema):
    name: str
    description: Optional[str]
    secret_key: str = Field(default_factory=token_urlsafe)
    webhook_url: Optional[HttpUrl]


class Client(BaseDocument):
    class Config:
        db = current_app.config['MONGODB_DATABASE']
        collection_name = 'clients'
        fields = ClientSchema.get_field_names()
        

