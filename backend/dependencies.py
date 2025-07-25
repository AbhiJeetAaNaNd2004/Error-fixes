# This file holds shared application state that can be imported by any other module
# without causing circular dependencies.

from typing import Dict

# This dictionary will be populated by main.py on startup and will hold
# the live instance of our FaceTrackingSystem.
app_state: Dict = {}
