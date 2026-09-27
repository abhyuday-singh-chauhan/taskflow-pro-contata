from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(Text, nullable=True)

    status = Column(
        String,
        default="backlog",
        nullable=False
    )

    start_date = Column(String, nullable=True)

    end_date = Column(String, nullable=True)

    position = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)

    task_id = Column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False
    )

    depends_on_task_id = Column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False
    )