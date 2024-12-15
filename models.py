# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=True)
    expiration_days = Column(Integer, default=60)  # Новое поле
    members = relationship("Member", back_populates="group", cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship("Group", back_populates="members")