"""
Configuration file for Combat Simulation System
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data files
DATA_DIR = os.path.join(BASE_DIR, 'data')
OBJECTS_FILE = os.path.join(DATA_DIR, 'objects.xlsx')
RULES_FILE = os.path.join(DATA_DIR, 'sets.xlsx')

# MBTiles configuration
MBTILES_PATH = "d:\horizondata\map\Топо.mbtiles"  # Update this path as needed

# Flask configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = True

# Simulation parameters
DEFAULT_STEP_INTERVAL = 500  # milliseconds
MAX_STEPS = 1000

# Map configuration
DEFAULT_CENTER = [36.3, 47.6]  # [lon, lat]
DEFAULT_ZOOM = 8
MIN_ZOOM = 0
MAX_ZOOM = 22

# Unit visualization colors (RGB hex)
UNIT_COLORS = {
    'tank': '#ff0000',        # Red
    'bmp': '#ff9900',         # Orange
    'infantry': '#00ff00',    # Green
    'mortar': '#0099ff',      # Light blue
    'artillery': '#0000ff',   # Blue
    'uav': '#9900ff'          # Purple
}

# Side colors
SIDE_COLORS = {
    'A': '#0066ff',  # Blue
    'B': '#ff3333'   # Red
}

# Combat potential values for each unit type
UNIT_POTENTIAL = {
    'infantry': 0.5,
    'bmp': 2.0,
    'tank': 6.0,
    'mortar': 2.0,
    'artillery': 3.0,
    'uav': 4.0
}

# Victory condition: side loses when potential drops to this percentage
DEFEAT_POTENTIAL_THRESHOLD = 0.30  # 30% of initial potential

# Logging configuration
LOGGING_ENABLED = True  # Enable/disable logging system
LOG_DIR = os.path.join(BASE_DIR, 'logs')  # Directory for all log files
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENABLE_CONSOLE_OUTPUT = False  # Console output (can slow down, disable for production)
DETAILED_COMBAT_LOG = True  # Log every combat event to JSON file
PERFORMANCE_LOGGING = False  # Log performance metrics (enable for optimization)

# Database settings (for future expansion)
DATABASE_ENABLED = False
DATABASE_PATH = os.path.join(BASE_DIR, 'simulation.db')
