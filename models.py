import os

from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from common import utilities

load_dotenv("dev.env")

database_name = os.getenv("database")
varchar_length = int(os.getenv("varchar_length"))
DATETIME = DATETIME(fsp=int(os.getenv("time_fsp")))
Base = declarative_base()

action_categories = [
    "start channel",
    "end channel",
    "start stream",
    "end stream",
    "start video",
    "end video",
    "start voice",
    "end voice",
    # Currently timer logs are not implemented
    # "start timer", "end timer"
]


class User(Base):
    # Question - How to make it just use the class name instead of hard coding the table name?
    __tablename__ = "user"
    id = Column(BIGINT, primary_key=True)
    # username = Column(String(32))
    # tag = Column(String(32))
    longest_streak = Column(INTEGER, server_default="0")
    current_streak = Column(INTEGER, server_default="0")
    def __repr__(self):
        return "<User(id='%s', longest='%s', current='%s')>" % (self.id, self.longest_streak, self.current_streak)


class Action(Base):
    __tablename__ = "action"
    id = Column(INTEGER, primary_key=True)
    user_id = Column(
        BIGINT, ForeignKey("user.id", onupdate="CASCADE"), nullable=False, index=True
    )
    category = Column(String(varchar_length), nullable=False)
    detail = Column(
        BIGINT
    )  # Currently, detail is the id of the channel where actions happen
    creation_time = Column(DATETIME, default=utilities.get_time)

    user = relationship("User", back_populates="action")


# This must be in global scope for correct models
User.action = relationship("Action", order_by=Action.id, back_populates="user")

if __name__ == "__main__":
    utilities.recreate_db(Base)
