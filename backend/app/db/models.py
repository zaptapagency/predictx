from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Prediction(Base):
    """Store prediction records"""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    vertical = Column(String)
    prediction_type = Column(String)
    features = Column(JSON)
    prediction = Column(Float)
    confidence = Column(Float)
    explanation = Column(JSON, nullable=True)
    recommendation = Column(String, nullable=True)
    model_version = Column(String)
    inference_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BatchJob(Base):
    """Store batch prediction jobs"""

    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    vertical = Column(String)
    prediction_type = Column(String)
    total_records = Column(Integer)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    results_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Upload(Base):
    """Store file uploads"""

    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    file_type = Column(String)  # csv, xlsx, etc.
    file_size = Column(Integer)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    rows_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class Model(Base):
    """Store model metadata"""

    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    vertical = Column(String, nullable=True)
    model_type = Column(String)  # universal, adapter
    is_active = Column(Boolean, default=True)
    accuracy = Column(Float, nullable=True)
    feature_count = Column(Integer)
    training_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """Store user information"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
