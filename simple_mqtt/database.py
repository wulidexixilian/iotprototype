import sqlite3
import os


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(
                         os.path.join(
                                      os.path.dirname(os.path.abspath(__file__)),
                                      'simple_mqtt.db'
                                      )
                         )
    rv.row_factory = sqlite3.Row
    return rv
