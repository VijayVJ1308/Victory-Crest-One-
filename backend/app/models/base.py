"""Victory Crest One - Database Base Model
Common declarative base with UUID primary keys, audit timestamps, and soft-delete support.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModelMixin:
    """Reusable model mixin for enterprise data integrity and auditability."""
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def to_dict(self):
        """Serialize model attributes to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
