"""
SQLAlchemy declarative base.
All ORM models inherit from Base defined here.
Shared across the entire db layer.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
