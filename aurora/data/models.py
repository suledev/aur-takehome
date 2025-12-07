from sqlmodel import SQLModel, Field
from datetime import datetime


class Message(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str
    user_name: str
    timestamp: datetime
    message: str