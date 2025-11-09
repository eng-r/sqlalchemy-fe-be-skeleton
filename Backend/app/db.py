from sqlalchemy import create_engine
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import DeclarativeBase, Session as SASession, sessionmaker
from sqlalchemy.sql import Executable

from .auth import get_active_principal
from .config import settings

from sqlalchemy import Select
from sqlalchemy.sql.elements import TextClause

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)


class AccessControlledSession(SASession):
    """Session subclass enforcing per-user access levels."""

    def _require_write_access(self, operation: str) -> None:
        principal = get_active_principal()
        if principal is None or principal.access.can_write:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"User '{principal.username}' requires write access to perform "
                f"'{operation}'."
            ),
        )

    @staticmethod
    def _is_select_statement(statement) -> bool:
        # SQLAlchemy Core/ORM Select
        if isinstance(statement, Select):
            return True
        # Raw text() queries
        if isinstance(statement, TextClause):
            return statement.text.lstrip().upper().startswith("SELECT")
        # Fallback for anything that exposes .is_select (defensive)
        is_sel = getattr(statement, "is_select", None)
        if isinstance(is_sel, bool):
            return is_sel
        return False

    def execute(self, statement, *args, **kwargs):  # type: ignore[override]
        principal = get_active_principal()
        if (
            principal is not None
            and not principal.access.can_write
            and not self._is_select_statement(statement)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User '{principal.username}' cannot execute write statements "
                    "with read-only access."
                ),
            )
        return super().execute(statement, *args, **kwargs)

    def add(self, instance, _warn: bool = True):  # type: ignore[override]
        self._require_write_access("add")
        return super().add(instance, _warn=_warn)

    def add_all(self, instances, _warn: bool = True):  # type: ignore[override]
        self._require_write_access("add_all")
        return super().add_all(instances, _warn=_warn)

    def delete(self, instance):  # type: ignore[override]
        self._require_write_access("delete")
        return super().delete(instance)

    def commit(self):  # type: ignore[override]
        self._require_write_access("commit")
        return super().commit()

    def flush(self, objects=None):  # type: ignore[override]
        self._require_write_access("flush")
        return super().flush(objects)

    def merge(self, instance, load: bool = True):  # type: ignore[override]
        self._require_write_access("merge")
        return super().merge(instance, load=load)

    def bulk_save_objects(self, objects, return_defaults=False, update_changed_only=True, render_nulls=False):  # type: ignore[override]
        self._require_write_access("bulk_save_objects")
        return super().bulk_save_objects(
            objects,
            return_defaults=return_defaults,
            update_changed_only=update_changed_only,
            render_nulls=render_nulls,
        )

    def bulk_insert_mappings(self, mapper, mappings, render_nulls=False):  # type: ignore[override]
        self._require_write_access("bulk_insert_mappings")
        return super().bulk_insert_mappings(mapper, mappings, render_nulls=render_nulls)

    def bulk_update_mappings(self, mapper, mappings):  # type: ignore[override]
        self._require_write_access("bulk_update_mappings")
        return super().bulk_update_mappings(mapper, mappings)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    class_=AccessControlledSession,
)


class Base(DeclarativeBase):
    pass
