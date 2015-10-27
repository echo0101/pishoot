from flask import g
from multiprocessing import Pool
from pishoot import app

def get_pool():
  pool = getattr(g, '_pool', None) 
  if pool is None:
    pool = Pool(processes=2)
  return pool

@app.teardown_appcontext
def teardown_pool(exception):
  pool = getattr(g, '_pool', None)
  if pool is not None:
    pool.join(60)
    pool.terminate()
