from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    SQLAlchemy uses this to keep track of tables and mappings.
    """
    pass


class Pokemon(Base):
    """
    ORM model for the 'pokemon' table.

    Mirrors the required schema :
    - pokemon_id (PK)
    - name
    - base_experience
    - height
    - order
    - weight
    - location_area_encounters
    """
    __tablename__ = "pokemon"

    pokemon_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_experience: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    # 'order' is a reserved word in SQL, so we specify the column name explicitly
    order: Mapped[int | None] = mapped_column("order", Integer)
    weight: Mapped[int | None] = mapped_column(Integer)
    location_area_encounters: Mapped[str | None] = mapped_column(Text)
