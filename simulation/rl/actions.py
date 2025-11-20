"""
Action space definition for RL agents
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


class ActionSpace:
    """Defines and processes actions for RL agents"""

    # Action types
    ACTION_MOVE_NORTH = 0
    ACTION_MOVE_SOUTH = 1
    ACTION_MOVE_EAST = 2
    ACTION_MOVE_WEST = 3
    ACTION_MOVE_NE = 4
    ACTION_MOVE_NW = 5
    ACTION_MOVE_SE = 6
    ACTION_MOVE_SW = 7
    ACTION_STAY = 8
    ACTION_ATTACK_NEAREST = 9
    ACTION_ATTACK_WEAKEST = 10
    ACTION_ATTACK_STRONGEST = 11
    ACTION_RETREAT = 12

    def __init__(self):
        """Initialize action space"""
        # Discrete action space with 13 actions
        self.action_space = spaces.Discrete(13)

    def get_action_space(self):
        """Return the action space"""
        return self.action_space

    def execute_action(self, agent, action, model):
        """
        Execute the chosen action

        Args:
            agent: The agent executing the action
            action: Action index (0-12) or numpy array
            model: The simulation model

        Returns:
            bool: True if action was successful
        """
        if not agent.is_alive:
            return False

        # Convert numpy array to int if needed
        if hasattr(action, 'item'):
            action = int(action.item())
        else:
            action = int(action)

        # Movement actions (0-8)
        if action <= 8:
            return self._execute_movement(agent, action)

        # Attack actions (9-11)
        elif action <= 11:
            return self._execute_attack(agent, action, model)

        # Retreat action (12)
        elif action == 12:
            return self._execute_retreat(agent, model)

        return False

    def _execute_movement(self, agent, action):
        """Execute movement action"""
        # Movement directions
        movements = {
            self.ACTION_MOVE_NORTH: (0, 1),
            self.ACTION_MOVE_SOUTH: (0, -1),
            self.ACTION_MOVE_EAST: (1, 0),
            self.ACTION_MOVE_WEST: (-1, 0),
            self.ACTION_MOVE_NE: (0.707, 0.707),
            self.ACTION_MOVE_NW: (-0.707, 0.707),
            self.ACTION_MOVE_SE: (0.707, -0.707),
            self.ACTION_MOVE_SW: (-0.707, -0.707),
            self.ACTION_STAY: (0, 0)
        }

        if action in movements:
            dx, dy = movements[action]

            # Apply movement with speed
            new_x = agent.pos[0] + dx * agent.speed
            new_y = agent.pos[1] + dy * agent.speed

            agent.pos = (new_x, new_y)

            # Update direction if moving
            if dx != 0 or dy != 0:
                agent.direction = np.degrees(np.arctan2(dy, dx))

            return True

        return False

    def _execute_attack(self, agent, action, model):
        """Execute attack action"""
        # Get enemies in range
        enemies = [a for a in model.agents
                  if a.side != agent.side and a.is_alive]

        if not enemies:
            return False

        # Filter by range
        enemies_in_range = [
            e for e in enemies
            if agent.calculate_distance(e.pos) <= agent.attack_range
        ]

        if not enemies_in_range:
            return False

        target = None

        # Attack nearest
        if action == self.ACTION_ATTACK_NEAREST:
            target = min(enemies_in_range,
                        key=lambda e: agent.calculate_distance(e.pos))

        # Attack weakest (lowest HP)
        elif action == self.ACTION_ATTACK_WEAKEST:
            target = min(enemies_in_range, key=lambda e: e.hp)

        # Attack strongest (highest HP)
        elif action == self.ACTION_ATTACK_STRONGEST:
            target = max(enemies_in_range, key=lambda e: e.hp)

        # Execute attack
        if target:
            agent.target = target
            return agent.attack(target)

        return False

    def _execute_retreat(self, agent, model):
        """Execute retreat - move away from nearest enemy"""
        enemies = [a for a in model.agents
                  if a.side != agent.side and a.is_alive]

        if not enemies:
            return False

        # Find nearest enemy
        nearest_enemy = min(enemies,
                           key=lambda e: agent.calculate_distance(e.pos))

        # Move away from enemy
        dx = agent.pos[0] - nearest_enemy.pos[0]
        dy = agent.pos[1] - nearest_enemy.pos[1]

        # Normalize direction
        distance = np.sqrt(dx**2 + dy**2)
        if distance > 0:
            dx /= distance
            dy /= distance

            # Move in opposite direction
            agent.pos = (
                agent.pos[0] + dx * agent.speed * 1.5,  # 1.5x speed for retreat
                agent.pos[1] + dy * agent.speed * 1.5
            )

            agent.direction = np.degrees(np.arctan2(dy, dx))

            return True

        return False

    def get_action_mask(self, agent, model):
        """
        Get mask of valid actions

        Args:
            agent: The agent
            model: The simulation model

        Returns:
            np.array: Boolean mask of valid actions
        """
        mask = np.ones(13, dtype=bool)

        # Check if can attack (enemies in range)
        enemies_in_range = any(
            a.side != agent.side and
            a.is_alive and
            agent.calculate_distance(a.pos) <= agent.attack_range
            for a in model.agents
        )

        # Disable attack actions if no enemies in range
        if not enemies_in_range:
            mask[self.ACTION_ATTACK_NEAREST] = False
            mask[self.ACTION_ATTACK_WEAKEST] = False
            mask[self.ACTION_ATTACK_STRONGEST] = False

        # Check if can retreat (enemies exist)
        enemies_exist = any(
            a.side != agent.side and a.is_alive
            for a in model.agents
        )

        if not enemies_exist:
            mask[self.ACTION_RETREAT] = False

        return mask

    def action_to_string(self, action):
        """Convert action index to human-readable string"""
        # Convert numpy array to int if needed
        if hasattr(action, 'item'):
            action = int(action.item())
        else:
            action = int(action)

        action_names = {
            0: "Move North",
            1: "Move South",
            2: "Move East",
            3: "Move West",
            4: "Move NE",
            5: "Move NW",
            6: "Move SE",
            7: "Move SW",
            8: "Stay",
            9: "Attack Nearest",
            10: "Attack Weakest",
            11: "Attack Strongest",
            12: "Retreat"
        }
        return action_names.get(action, "Unknown")
