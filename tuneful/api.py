import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path

# JSON schema describing the structure of a song
song_schema = {
  "type": "object",
  "properties": {
    "file": {
      "type": "object",
      "properties": {
        "id": {"type": "number"}
      },
    },
  },  
  "required": ["file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
  """ Get a list of songs """
  # Get the songs from the database
  songs = session.query(models.Song).all()
  
  # Convert songs to JSON and return a response
  data = json.dumps([song.as_dictionary() for song in songs])
  return Response(data, 200, mimetype="application/json")
  
@app.route("/api/song/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def song_get(id):
  """ Single song endpoint """
  song = session.query(models.Song).get(id)
  
  # Check if song exists
  # if not return a 404 with a helpful message
  if not song:
    message = "Could not find the song with id {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 404, mimetype="application/json")
    
  # return the song as JSON
  data = json.dumps(song.as_dictionary())
  return Response(data, 200, mimetype="application/json")
  
@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
  """ Add a new song """
  data = request.json
  
  # check that the json supplied is valid
  # if not return a 422 Unprocessable Entry
  try:
    validate(data, song_schema)
  except ValidationError as error:
    data = {"message": error.message}
    return Response(json.dumps(data), 422, mimetype="application/json")
    
  # add the song to the database
  song = models.Song(song_file_id=data["file"]["id"])
  session.add(song)
  session.commit()
  
  # return a 201 Created
  # containing the post as JSON and with the
  # location header set to the location of the song
  data = json.dumps(song.as_dictionary())
  headers = {"Location": url_for("songs_get", id=song.id)}
  
  return Response(data, 201, headers=headers, mimetype="application/json")
