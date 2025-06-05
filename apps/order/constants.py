from enum import Enum


class OrderWebsocketEvent(Enum):
    UPDATED = 'updated'
    CREATED = 'created'
