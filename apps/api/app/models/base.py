import json

from sqlalchemy import Text, TypeDecorator, types
from sqlalchemy.orm import DeclarativeBase


class JSONType(TypeDecorator):
    """A JSON type that works with both PostgreSQL (JSONB) and SQLite (TEXT)."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())


class UUIDType(TypeDecorator):
    """A UUID type that works with both PostgreSQL and SQLite."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            import uuid as _uuid

            return _uuid.UUID(value) if not isinstance(value, _uuid.UUID) else value
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID

            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(Text())


class Base(DeclarativeBase):
    pass
