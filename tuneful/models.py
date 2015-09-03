import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from tuneful import app
from database import Base, engine, session

class Song(Base):
  """ 
    The Song model: 
    This should have an integer id column, and a column specifying 
    a one-to-one relationship with a File.
  """
  __tablename__ = "songs"
  
  id = Column(Integer, primary_key=True)
  song_file_id = Column(Integer, ForeignKey("files.id"), nullable=False)

  def as_dictionary(self):
    song_file_id = session.query(File).filter_by(id=self.song_file_id).first()
    return {
      "id": self.id,
      "file": {
        "id": song_file_id.id,
        "name": song_file_id.filename
      }
    }

class File(Base):
  """
    The File model: 
    This should have an integer id column, a string column for the 
    filename, and the backref from the one-to-one relationship with 
    the Song.
  """
  __tablename__ = "files"
  
  id = Column(Integer, primary_key=True)
  filename = Column(String(1024))
  song = relationship("Song", backref="song", uselist=False)

  def as_dictionary(self):
    file = {
      "id": self.id,
      "name": self.filename,
      "path": url_for("uploaded_file", filename=self.filename)
    }
    return file