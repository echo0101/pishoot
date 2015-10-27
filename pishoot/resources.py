from flask import request
from flask_restful import Resource, reqparse
from pishoot import app, game, models 

class Leaderboard(Resource):
  def get(self):
    retval = []
    position = 1
    for leader in models.get_leaders():
      v = {"name": leader.name, "score": leader.score, "position": position}
      position+=1
      retval.append(v)
    return retval

class Queue(Resource):
  def _get_parser(self):
    parser = reqparse.RequestParser()
    parser.add_argument('name', required=True, help="Player's name")
    parser.add_argument('email', help="Player's email")
    return parser

  def get(self):
    current = game.get_players_in_game()
    queue = models.get_queue()
    return {"current": current, "queue": map(lambda player: {"name":player.name}, queue)}
  
  def post(self):
    args = self._get_parser().parse_args()
    player = game.queue_player(args['name'], args['email'])
    return {"status": "success", "id": player.id}, 201

class GameManage(Resource):
  def _get_parser(self):
    parser = reqparse.RequestParser()
    parser.add_argument('game', required=True, help='Game id to apply action to')
    parser.add_argument('action', required=True, help='Action can be start, skip or abort')
    return parser

  def put(self):
    args = self._get_parser().parse_args()

    return {
        'start': game.start_game,
        'skip': game.skip_player, 
        'abort': game.abort,
    } [args['action']](args['game'])



