from flask import Flask, jsonify
from flask_restful import Resource, Api
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SELF_TEST'] = False 

app.config['SECRET_KEY'] = 'sup3r-$ecret'
app.config['API_KEY'] = 'sup3r-$ecret'
app.config['MY_URL'] = 'http://localhost:5000'

app.config['APP_LOG'] = 'pishoot.log'

# db config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/pi/pishoot/pishoot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# load local config
app.config.from_pyfile('../my.cfg', silent=True)

db = SQLAlchemy(app)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler 

    # log file
    file_handler = RotatingFileHandler(app.config['APP_LOG'],maxBytes=30000000)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

import pishoot.game

# configure pin#s in game.py
game.init_pins()

import pishoot.resources

api = Api(app)

api.add_resource(resources.Leaderboard, '/leaderboard')
api.add_resource(resources.Queue, '/queue')
api.add_resource(resources.GameManage, '/game')

import pishoot.error

@app.errorhandler(error.InvalidAPIUsage)
def handle_invalid_usage(error):
  response = jsonify(error.to_dict())
  response.status_code = error.status_code
  return response

@app.before_first_request
def dbinit():
  # ensure db created
  db.create_all()
  db.session.commit()
