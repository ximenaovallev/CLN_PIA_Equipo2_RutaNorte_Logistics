"""Creación del motor y de la fábrica de sesiones a partir de DATABASE_URL (12-Factor)."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .tablas import metadata


def normalizar_url(url: str) -> str:
    """Acepta las formas que usan las plataformas (`postgres://`, `postgresql://`) y fija el driver psycopg 3."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def crear_motor(url: str) -> Engine:
    url = normalizar_url(url)
    if url.startswith("sqlite"):
        # SQLite en memoria vive por conexión: un único pool compartido para que todas las sesiones lo vean.
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url, pool_pre_ping=True)


def crear_fabrica_de_sesiones(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, expire_on_commit=False)


def crear_tablas(motor: Engine) -> None:
    metadata.create_all(motor)
