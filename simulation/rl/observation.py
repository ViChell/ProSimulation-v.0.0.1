"""
Observation space builder for RL agents
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


class ObservationBuilder:
    """Builds observation space for RL agents"""

    def __init__(self, max_enemies=20, max_allies=20):
        """
        Initialize observation builder

        Args:
            max_enemies: Maximum number of enemies to observe
            max_allies: Maximum number of allies to observe
        """
        self.max_enemies = max_enemies
        self.max_allies = max_allies

        # Observation space dimensions
        self.self_state_dim = 10  # Own state features
        self.enemy_feature_dim = 8  # Features per enemy
        self.ally_feature_dim = 8   # Features per ally

        total_dim = (
            self.self_state_dim +
            self.max_enemies * self.enemy_feature_dim +
            self.max_allies * self.ally_feature_dim
        )

        # Define observation space
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(total_dim,),
            dtype=np.float32
        )

    def build_observation(self, agent, model):
        """
        Build observation vector for agent

        Args:
            agent: The agent to build observation for
            model: The simulation model

        Returns:
            np.array: Observation vector
        """
        observation = []

        # 1. Self state (10 features)
        self_state = self._get_self_state(agent)
        observation.extend(self_state)

        # 2. Enemy states (max_enemies * 8 features)
        enemies = self._get_enemies(agent, model)
        enemy_features = self._encode_units(agent, enemies, self.max_enemies)
        observation.extend(enemy_features)

        # 3. Ally states (max_allies * 8 features)
        allies = self._get_allies(agent, model)
        ally_features = self._encode_units(agent, allies, self.max_allies)
        observation.extend(ally_features)

        return np.array(observation, dtype=np.float32)

    def _get_self_state(self, agent):
        """Get agent's own state features"""
        return [
            agent.pos[0],                          # x position
            agent.pos[1],                          # y position
            agent.hp / agent.max_hp,               # normalized HP
            agent.attack_power / 100.0,            # normalized attack power
            agent.attack_range / 20.0,             # normalized range
            agent.accuracy,                        # accuracy
            agent.armor / 50.0,                    # normalized armor
            agent.speed / 0.01,                    # normalized speed
            np.sin(np.radians(agent.direction)),   # direction sin
            np.cos(np.radians(agent.direction))    # direction cos
        ]

    def _get_enemies(self, agent, model):
        """Get list of enemy units"""
        enemies = [a for a in model.agents
                  if a.side != agent.side and a.is_alive]

        # Sort by distance
        enemies.sort(key=lambda e: agent.calculate_distance(e.pos))

        return enemies[:self.max_enemies]

    def _get_allies(self, agent, model):
        """Get list of allied units"""
        allies = [a for a in model.agents
                 if a.side == agent.side and a.is_alive and a.unit_id != agent.unit_id]

        # Sort by distance
        allies.sort(key=lambda a: agent.calculate_distance(a.pos))

        return allies[:self.max_allies]

    def _encode_units(self, agent, units, max_count):
        """
        Encode units into feature vectors

        Args:
            agent: The observing agent
            units: List of units to encode
            max_count: Maximum number of units to encode

        Returns:
            list: Flat list of features
        """
        features = []

        for i in range(max_count):
            if i < len(units):
                unit = units[i]
                features.extend(self._encode_single_unit(agent, unit))
            else:
                # Padding for missing units
                features.extend([0.0] * self.enemy_feature_dim)

        return features

    def _encode_single_unit(self, agent, unit):
        """Encode single unit into features"""
        # Relative position
        dx = unit.pos[0] - agent.pos[0]
        dy = unit.pos[1] - agent.pos[1]
        distance = agent.calculate_distance(unit.pos)

        # Unit type encoding (one-hot would be better, but keeping simple)
        unit_type_encoding = self._encode_unit_type(unit.unit_type)

        return [
            dx * 100,                           # relative x (scaled)
            dy * 100,                           # relative y (scaled)
            distance,                           # distance in km
            unit.hp / unit.max_hp,             # normalized HP
            unit_type_encoding,                 # unit type
            unit.attack_power / 100.0,         # normalized attack power
            unit.attack_range / 20.0,          # normalized range
            1.0 if distance <= agent.attack_range else 0.0  # in range flag
        ]

    def _encode_unit_type(self, unit_type):
        """Encode unit type as number"""
        type_map = {
            'tank': 0.0,
            'bmp': 0.2,
            'infantry': 0.4,
            'mortar': 0.6,
            'artillery': 0.8,
            'uav': 1.0
        }
        return type_map.get(unit_type, 0.0)

    def get_observation_space(self):
        """Return the observation space"""
        return self.observation_space
