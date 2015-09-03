import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
  """ Tests for the tuneful API """

  def setUp(self):
    """ Test setup """
    self.client = app.test_client()

    # Set up the tables in the database
    Base.metadata.create_all(engine)

    # Create folder for test uploads
    os.mkdir(upload_path())

  def tearDown(self):
    """ Test teardown """
    session.close()
    # Remove the tables and their data from the database
    Base.metadata.drop_all(engine)
  
    # Delete test upload folder
    shutil.rmtree(upload_path())
    
  def test_get_empty_songs(self):
    """ Getting songs from an empty database """
    response = self.client.get("/api/songs", 
      headers=[("Accept", "application/json")]
    )
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.mimetype, "application/json")
    
    data = json.loads(response.data)
    self.assertEqual(data, [])
  
  def test_get_songs(self):
    fileA = models.File(filename="FileA")
    fileB = models.File(filename="FileB")
    
    session.add_all([fileA, fileB])
    session.commit()
    
    songA = models.Song(song_file_id=fileA.id)
    songB = models.Song(song_file_id=fileB.id)
    
    session.add_all([songA, songB])
    session.commit()
    
    response = self.client.get("/api/songs",
      headers=[("Accept", "application/json")]
    )
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.mimetype, "application/json")
    
    data = json.loads(response.data)
    self.assertEqual(len(data), 2)
    
    songA = data[0]
    self.assertEqual(songA["id"], 1)
    self.assertEqual(songA["file"]["id"], 1)
    self.assertEqual(songA["file"]["name"], "FileA")
    
    songB = data[1]
    self.assertEqual(songB["id"], 2)
    self.assertEqual(songB["file"]["id"], 2)
    self.assertEqual(songB["file"]["name"], "FileB")
    
  def test_get_non_existent_song(self):
    """ Get a single song which doesn't exist """
    response = self.client.get("/api/song/1",
      headers=[("Accept", "application/json")]
    )
    
    self.assertEqual(response.status_code, 404)
    self.assertEqual(response.mimetype, "application/json")
    
    data = json.loads(response.data)
    self.assertEqual(data["message"], "Could not find the song with id 1")
    
  def test_song_post(self):
    """ Post a new song """
    fileA = models.File(filename="FileA")
    
    session.add(fileA)
    session.commit()
    
    data = {
      "file": {
        "id": fileA.id
      }
    }
    
    response = self.client.post("api/songs",
      data=json.dumps(data),
      content_type="application/json",
      headers=[("Accept", "application/json")]
    )
    
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.mimetype, "application/json")
    self.assertEqual(urlparse(response.headers.get("Location")).path, "/api/songs")
    
    data = json.loads(response.data)
    self.assertEqual(data["id"], fileA.id)
    
    songs = session.query(models.Song).all()
    self.assertEqual(len(songs), 1)
    
    song = songs[0]
    self.assertEqual(song.id, fileA.id)
    
if __name__ == "__main__":
  unittest.main()    