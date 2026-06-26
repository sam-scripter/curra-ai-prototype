from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from database import Base


class Document(Base):
    """
    One row per file ingested into the knowledge base.
    Tracks the filename, which course it belongs to, when it was uploaded,
    and how many chunks were created from it.
    """
    __tablename__ = "documents"

    id             = Column(Integer, primary_key=True, index=True)
    filename       = Column(String, nullable=False)
    # unit_namespace scopes this document to a specific course and cohort.
    # For the prototype this is always 'curra_dav_2026_s1'.
    # In the full system this becomes the isolation mechanism between courses.
    unit_namespace = Column(String, nullable=False, default="curra_dav_2026_s1")
    uploaded_at    = Column(DateTime(timezone=True), server_default=func.now())
    chunk_count    = Column(Integer, default=0)

    # One document produces many chunks. Deleting a document cascades
    # and removes all its chunks from the vector store automatically.
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """
    One row per text segment extracted from a document.
    This is the core table — what gets searched on every student query.
    
    The embedding column stores a 1536-dimensional float vector produced
    by OpenAI's text-embedding-3-small model. pgvector stores it efficiently
    and supports cosine similarity search against it.
    """
    __tablename__ = "chunks"

    id             = Column(Integer, primary_key=True, index=True)
    document_id    = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content        = Column(Text, nullable=False)       # the raw text of this chunk
    embedding      = Column(Vector(1536))               # 1536 = text-embedding-3-small dimensions
    chunk_index    = Column(Integer, nullable=False)    # position of this chunk within the document
    page_number    = Column(Integer, nullable=True)     # slide or page number for citations
    unit_namespace = Column(String, nullable=False, default="curra_dav_2026_s1")

    document = relationship("Document", back_populates="chunks")


class Gap(Base):
    """
    One row per question the AI could not answer confidently.
    
    When a student query returns a similarity score below 0.5,
    the query is logged here rather than silently ignored.
    The lecturer demo dashboard reads from this table to show
    which topics the course materials don't cover adequately.
    """
    __tablename__ = "gaps"

    id             = Column(Integer, primary_key=True, index=True)
    query          = Column(Text, nullable=False)
    unit_namespace = Column(String, nullable=False, default="curra_dav_2026_s1")
    confidence     = Column(Float, nullable=False)  # the best similarity score achieved (0.0 – 1.0)
    asked_at       = Column(DateTime(timezone=True), server_default=func.now())