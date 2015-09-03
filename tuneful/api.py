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
  
@app.route("/api/song/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def update_song(id):
  """ Single song update endpoint """
  
  # get the song from the database
  song = session.query(models.Song).get(id)
  
  # cehck if the song exisits
  # if not return a 404 with a helpful message
  if not song:
    message = "Could not find the song with id {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 404, mimetype="application/json")
    
  data = request.json
  
  # check that the JSON supplied is valid
  # if not return a 422 Unprocessable Entry
  try:
    validate(data, song_schema)
  except ValidationError as error:
    data = {"message": error.message}
    return Response(json.dumps(data), 422, mimetype="application/json")
    
  song.song_file_id = data["file"]["id"]
  session.commit()
  
  # return an OK 200
  # containing the song as JSON and with the
  # location header set to the location of the song
  data = json.dumps(song.as_dictionary())
  headers = {"Location": url_for("song_get", id=song.id)}
  return Response(data, 200, headers=headers, mimetype="application/json")
  
@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def song_delete(id):
  """ Single song delete endpoint """
  
  # get the song from the database
  song = session.query(models.Song).get(id)
  
  # check if song exists
  # if not return a 404 with a helpful message
  if not song:
    message = "Could not find song with id {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 404, mimetype="application/json")
    
  # successfully delete song
  message = "Successfully deleted song with id {}".format(id)
  data = json.dumps({"message": message, "song": song.as_dictionary()})
  
  session.delete(song)
  session.commit()
  
  return Response(data, 200, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
  return send_from_directory(upload_path(), filename)
  
@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
  file = request.files.get("file")
  
  if not file:
    message = "Could not find file data"
    data = {"message": message}
    return Response(json.dumps(data), 422, mimetype="application/json")
    
  filename = secure_filename(file.filename)
  db_file = models.File(filename=filename)
  session.add(db_file)
  session.commit()
  file.save(upload_path(filename))
  
  data = db_file.as_dictionary()
  return Response(json.dumps(data), 201, mimetype="application/json")