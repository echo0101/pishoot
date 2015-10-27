from pishoot import db 
import datetime

class Player(db.Model):
  __tablename__ = "players"
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(80))
  email = db.Column(db.String(120))
  signup_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  game_id = db.Column(db.String(80), default="")
  in_queue = db.Column(db.Boolean, default=True)
  play_time = db.Column(db.DateTime)
  score = db.Column(db.Integer)

  def __init__(self, name=None, email=None):
    self.name = name
    self.email = email

  def __repr__(self):
    return '<Player (%d) %r>' % (self.id, self.name)
 
def get_queue():
  return Player.query.filter_by(in_queue=True).filter_by(game_id="").order_by(Player.signup_time).all()

def get_next_in_queue():
  return Player.query.filter_by(in_queue=True).filter_by(game_id="").order_by(Player.signup_time).first()

def get_leaders():
  return Player.query.filter(Player.score>0).order_by(Player.score.desc()).limit(10).all()

def get_player_in_game(game_id):
  return Player.query.filter_by(in_queue=True).filter_by(game_id=game_id).order_by(Player.signup_time).first()


