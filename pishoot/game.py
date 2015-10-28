import RPi.GPIO as GPIO
from multiprocessing import Lock
from pishoot.error import InvalidAPIUsage
from pishoot import mp, db, models, app
import time,random,sys,datetime

GAME_A = "A"
GAME_B = "B"

GAME_STATE_READY = 0
GAME_STATE_ACTIVE = 1

TARGET_STATE_INACTIVE = 0
TARGET_STATE_ACTIVE = 1

GAMES = [GAME_A,GAME_B]
TARGET_PINS = {
    GAME_A: [(7,8), (11,10), (13,12), (15,16)], 
    GAME_B: [(19,18), (21,22), (23,24), (29,26)]
    }

GAME_STATE = None

GAME_LEN = 30 # seconds

def init_pins():
  GPIO.setmode(GPIO.BOARD)

  for game in GAMES:
    for pair in TARGET_PINS[game]:
      print game, " setting pair (%d,%d)" % pair
      GPIO.setup(pair[0], GPIO.OUT)
      GPIO.setup(pair[1], GPIO.IN) #TODO determine internal pull-up/down
      sys.stdout.flush()
    _clear_targets(game)
    _output_targets(game)

def get_game_state(game_id):
  global GAME_STATE
  if GAME_STATE is None:
    GAME_STATE = {}
    for game in GAMES:
      game_info = {"state": GAME_STATE_READY, "score": 0, "targets": [], "lock": Lock(), "player": None}
      for pairs in TARGET_PINS[game]:
        game_info["targets"].append({"target": pairs[0], "sensor": pairs[1], "state": TARGET_STATE_INACTIVE})
      GAME_STATE[game] = game_info

  if game_id not in GAME_STATE:
    raise InvalidAPIUsage("game id does not exist")

  return GAME_STATE[game_id]

def _game_runner(game_id):
  game_info = get_game_state(game_id)

  if not game_info['lock'].acquire(False):
    raise InvalidAPIUsage("game already in-progress (failed to acquire lock)")
  game_info['state'] = GAME_STATE_ACTIVE
  print game_info['state']

  _clear_targets(game_id)

  game_info["score"] = 0

  _set_target(game_id)
  time_start = time.time()

  while time.time() - time_start < GAME_LEN:
    time.sleep(1)

  _clear_targets(game_id)
  _output_targets(game_id)

  game_info['lock'].release()
  game_info['state'] = GAME_STATE_READY

  return {"game_id": game_id, "score": game_info["score"]}

def _record_result(result_info):
  player = models.get_player_in_game(result_info["game_id"])
  player.score = result_info["score"]
  player.in_queue = False
  db.session.add(player)
  db.session.commit()
  update_queue()

#callback for sensor event detect
def _record_hit(channel, game_id):
  print game_id, "recording hit on %d" % channel
  GPIO.remove_event_detect(channel)

  game_info = get_game_state(game_id)

  for target in game_info["targets"]:
    if target["sensor"] == channel:
      target["state"] = TARGET_STATE_INACTIVE
      GPIO.output(target["target"], GPIO.HIGH)
      game_info["score"] += 1

  time.sleep(1)
  _set_target(game_id)

# sets pinouts and event listeners
def _output_targets(game_id):
  game_info = get_game_state(game_id)
  for target in game_info['targets']:
    if target["state"] == TARGET_STATE_ACTIVE:
      GPIO.output(target["target"], GPIO.LOW)
      GPIO.add_event_detect(target["sensor"], GPIO.RISING, callback=lambda x:_record_hit(x,game_id), bouncetime=1000)
    else:
      GPIO.output(target["target"], GPIO.HIGH)
      GPIO.remove_event_detect(target["sensor"])

# sets all targets to inactive
def _clear_targets(game_id):
  game_info = get_game_state(game_id)
  for target in game_info['targets']:
    target["state"] = TARGET_STATE_INACTIVE

# randomly choose the next taret and set pinout
def _set_target(game_id):
  game_info = get_game_state(game_id)
  game_info["targets"][random.randrange(0, len(game_info['targets']))]["state"] = TARGET_STATE_ACTIVE
  _output_targets(game_id)

def start_game(game_id):
  game_info = get_game_state(game_id)
  if game_info['state'] == GAME_STATE_ACTIVE:
    raise InvalidAPIUsage("game already in-progress, abort to start a new game.")
  player = models.get_player_in_game(game_id)
  if player is None:
    raise InvalidAPIUsage("no player in game, queue player first.")
  player.play_time = datetime.datetime.utcnow()
  db.session.add(player)
  db.session.commit()
  pool = mp.get_pool()
  pool.apply_async(_game_runner, (game_id,), callback=_record_result)
  return {"status": "success"}

def skip_player(game_id):
  raise InvalidAPIUsage("not yet implemented", status_code=500)

def abort(game_id):
  raise InvalidAPIUsage("not yet implemented", status_code=500)

def update_queue():
  player = models.get_next_in_queue()
  for game in GAMES:
    if player is None:
      break
    game_info = get_game_state(game)
    if game_info['state']== GAME_STATE_READY and models.get_player_in_game(game) is None:
      player.game_id = game
      db.session.add(player)
      player = models.get_next_in_queue()
  db.session.commit()

def queue_player(name, email):
  player = models.Player(name, email)
  db.session.add(player)
  db.session.commit()
  update_queue()
  return player

def get_players_in_game():
  retval = []
  for game in GAMES:
    game_info = get_game_state(game)
    info = {"game_id":game}
    player = models.get_player_in_game(game)
    if player is not None:
      info["player"] = player.name
    else:
      info["player"] = ""
    info["state"] = "PLAYING" if game_info['state'] == GAME_STATE_ACTIVE else "READY"
    print "state at get players" , game, game_info['state']
    retval.append(info)
  return retval

#@app.teardown_appcontext
#def cleanup_gpio(exception):
#  print "cleaning up gpio"
#  GPIO.cleanup()

