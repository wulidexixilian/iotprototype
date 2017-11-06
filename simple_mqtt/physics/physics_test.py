from physics import model
import time

s = model.HydSystem()
d1 = s.to_dict()
# j = s.to_json()
# s.beat()
s.update({'.root._manipulator._cylinder._position$_signal'
: {'value': 100, 'time_stamp': time.clock()}})
d2 = s.to_dict()