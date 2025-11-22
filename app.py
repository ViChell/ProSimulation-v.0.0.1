from flask import Flask, jsonify, render_template, send_file
from flask_cors import CORS
import sqlite3
import io
import os
import signal
import sys

from simulation.model import CombatSimulation
from simulation.logging_config import SimulationLogger
import config

app = Flask(__name__)
CORS(app)

# Global simulation instance
sim = None

def init_simulation():
    """Initialize or reset the simulation"""
    global sim
    sim = CombatSimulation(
        objects_file=config.OBJECTS_FILE,
        rules_file=config.RULES_FILE
    )
    return sim

# Initialize simulation on startup
init_simulation()

# === MBTiles endpoints ===

@app.route('/tiles/<int:z>/<int:x>/<int:y>.png')
def get_tile(z, x, y):
    """Serve tiles from MBTiles file"""
    if not os.path.exists(config.MBTILES_PATH):
        return '', 404
    
    try:
        conn = sqlite3.connect(config.MBTILES_PATH)
        cursor = conn.cursor()
        
        # MBTiles uses TMS coordinates (Y is flipped)
        tms_y = (2**z - 1) - y
        
        cursor.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return send_file(
                io.BytesIO(result[0]),
                mimetype='image/png'
            )
        else:
            return '', 404
            
    except Exception as e:
        print(f"Tile error: {e}")
        return '', 404

@app.route('/tiles/metadata')
def get_metadata():
    """Get metadata from MBTiles"""
    if not os.path.exists(config.MBTILES_PATH):
        return jsonify({"error": "MBTiles file not found"}), 404
    
    try:
        conn = sqlite3.connect(config.MBTILES_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM metadata")
        
        metadata = {}
        for row in cursor.fetchall():
            metadata[row[0]] = row[1]
        
        conn.close()
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Simulation API endpoints ===

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/api/init', methods=['POST'])
def api_init():
    """Initialize new simulation"""
    try:
        init_simulation()
        return jsonify({
            'status': 'success',
            'message': 'Simulation initialized',
            'data': sim.get_state(),
            'statistics': sim.get_statistics()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/step', methods=['POST'])
def api_step():
    """Execute one simulation step"""
    try:
        if sim is None:
            return jsonify({'status': 'error', 'message': 'Simulation not initialized'}), 400
        
        sim.step()
        
        return jsonify({
            'status': 'success',
            'step': sim.step_count,
            'running': sim.running,
            'data': sim.get_state(),
            'statistics': sim.get_statistics()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/state', methods=['GET'])
def api_state():
    """Get current simulation state"""
    try:
        if sim is None:
            return jsonify({'status': 'error', 'message': 'Simulation not initialized'}), 400
        
        return jsonify({
            'status': 'success',
            'step': sim.step_count,
            'running': sim.running,
            'data': sim.get_state(),
            'statistics': sim.get_statistics()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset simulation to initial state"""
    try:
        init_simulation()
        return jsonify({
            'status': 'success',
            'message': 'Simulation reset',
            'data': sim.get_state(),
            'statistics': sim.get_statistics()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """Get detailed statistics"""
    try:
        if sim is None:
            return jsonify({'status': 'error', 'message': 'Simulation not initialized'}), 400
        
        return jsonify({
            'status': 'success',
            'statistics': sim.get_statistics(),
            'casualties': sim.get_casualties()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def api_config():
    """Get simulation configuration"""
    return jsonify({
        'status': 'success',
        'config': {
            'center': config.DEFAULT_CENTER,
            'zoom': config.DEFAULT_ZOOM,
            'min_zoom': config.MIN_ZOOM,
            'max_zoom': config.MAX_ZOOM,
            'step_interval': config.DEFAULT_STEP_INTERVAL,
            'max_steps': config.MAX_STEPS,
            'unit_colors': config.UNIT_COLORS,
            'side_colors': config.SIDE_COLORS
        }
    })

def cleanup_logging():
    """Gracefully shutdown logging system"""
    try:
        SimulationLogger.shutdown()
    except Exception as e:
        print(f"Error during logging shutdown: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down gracefully...")
    cleanup_logging()
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.DEBUG,
            use_reloader=False  # Вимкнути reloader щоб уникнути подвійної ініціалізації
        )
    finally:
        # Cleanup при нормальному завершенні
        cleanup_logging()
