"""
RL-controlled military unit
"""

from ..units import MilitaryUnit
from .actions import ActionSpace


class RLMilitaryUnit(MilitaryUnit):
    """
    Military unit controlled by reinforcement learning policy

    This class extends the base MilitaryUnit to allow control by an RL agent
    instead of the default scripted behavior.
    """

    def __init__(self, model, unit_id, name, side, unit_type, pos, speed, direction,
                 hp, max_hp, attack_range, attack_power, accuracy, armor, personnel_count=0,
                 policy=None):
        """
        Initialize RL-controlled unit

        Args:
            policy: RL policy function (observation -> action)
            All other args same as MilitaryUnit
        """
        super().__init__(
            model, unit_id, name, side, unit_type, pos, speed, direction,
            hp, max_hp, attack_range, attack_power, accuracy, armor, personnel_count
        )

        self.policy = policy
        self.action_space = ActionSpace()

        # Additional RL-specific tracking
        self.total_reward = 0.0
        self.episode_steps = 0

    def set_policy(self, policy):
        """Set or update the policy"""
        self.policy = policy

    def step(self):
        """
        Execute one step of behavior using RL policy

        If no policy is set, falls back to default behavior
        """
        if not self.is_alive:
            return

        self.episode_steps += 1

        # If policy is set, use RL behavior
        if self.policy is not None:
            self._rl_step()
        else:
            # Fall back to default scripted behavior
            super().step()

    def _rl_step(self):
        """Execute step using RL policy"""
        # This would be called by the environment
        # The environment handles observation building and action execution
        # This is a placeholder for when unit is used outside environment
        pass

    def get_state_summary(self):
        """Get summary of current state for RL"""
        return {
            'unit_id': self.unit_id,
            'name': self.name,
            'type': self.unit_type,
            'side': self.side,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'hp_ratio': self.hp / self.max_hp,
            'position': self.pos,
            'is_alive': self.is_alive,
            'kills': self.kills,
            'shots_fired': self.shots_fired,
            'hits_landed': self.hits_landed,
            'accuracy': self.hits_landed / self.shots_fired if self.shots_fired > 0 else 0,
            'total_reward': self.total_reward,
            'episode_steps': self.episode_steps
        }

    def add_reward(self, reward):
        """Track cumulative reward"""
        self.total_reward += reward

    def reset_episode(self):
        """Reset episode-specific tracking"""
        self.total_reward = 0.0
        self.episode_steps = 0


def create_rl_unit(model, unit_data, policy=None):
    """
    Factory function to create RL-controlled unit

    Args:
        model: Simulation model
        unit_data: Dictionary with unit parameters
        policy: RL policy (optional)

    Returns:
        RLMilitaryUnit instance
    """
    return RLMilitaryUnit(
        model=model,
        unit_id=unit_data['id'],
        name=unit_data['name'],
        side=unit_data['side'],
        unit_type=unit_data['type'],
        pos=(unit_data['x_coord'], unit_data['y_coord']),
        speed=unit_data['speed'],
        direction=unit_data['direction'],
        hp=unit_data['hp'],
        max_hp=unit_data['max_hp'],
        attack_range=unit_data['range'],
        attack_power=unit_data['attack_power'],
        accuracy=unit_data['accuracy'],
        armor=unit_data['armor'],
        personnel_count=unit_data['personnel_count'],
        policy=policy
    )
