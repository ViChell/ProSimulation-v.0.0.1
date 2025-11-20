"""
Reward calculator for RL agents
"""

import numpy as np


class RewardCalculator:
    """Calculates rewards for RL agents"""

    def __init__(self, config=None):
        """
        Initialize reward calculator

        Args:
            config: Dictionary with reward weights
        """
        # Default reward weights
        self.config = config or {
            'kill_reward': 10.0,           # Reward for killing enemy
            'hit_reward': 1.0,             # Reward for hitting enemy
            'miss_penalty': -0.1,          # Penalty for missing
            'damage_taken_penalty': -2.0,  # Penalty per HP lost
            'death_penalty': -50.0,        # Penalty for dying
            'survival_reward': 0.1,        # Reward per step survived
            'distance_penalty': -0.01,     # Penalty for being far from enemies
            'in_range_reward': 0.5,        # Reward for having enemy in range
            'retreat_penalty': -0.2,       # Small penalty for retreating
            'team_kill_reward': 5.0,       # Shared reward when ally kills
            'win_reward': 100.0,           # Bonus for winning battle
            'lose_penalty': -100.0         # Penalty for losing battle
        }

    def calculate_reward(self, agent, model, action_result):
        """
        Calculate reward for agent's action

        Args:
            agent: The agent
            model: The simulation model
            action_result: Dictionary with action outcome

        Returns:
            float: Reward value
        """
        reward = 0.0

        # 1. Survival reward
        if agent.is_alive:
            reward += self.config['survival_reward']
        else:
            # Death penalty
            reward += self.config['death_penalty']
            return reward  # Dead agents get no other rewards

        # 2. Combat rewards
        if action_result.get('attacked', False):
            if action_result.get('hit', False):
                reward += self.config['hit_reward']

                # Damage reward (proportional to damage dealt)
                damage_dealt = action_result.get('damage_dealt', 0)
                reward += damage_dealt * 0.1

                # Kill reward
                if action_result.get('killed', False):
                    reward += self.config['kill_reward']

            else:
                reward += self.config['miss_penalty']

        # 3. Damage taken penalty
        damage_taken = action_result.get('damage_taken', 0)
        if damage_taken > 0:
            reward += self.config['damage_taken_penalty'] * (damage_taken / agent.max_hp)

        # 4. Tactical positioning
        enemies_in_range = self._count_enemies_in_range(agent, model)
        if enemies_in_range > 0:
            reward += self.config['in_range_reward'] * enemies_in_range

        # 5. Distance to nearest enemy (encourage engagement)
        nearest_enemy_distance = self._get_nearest_enemy_distance(agent, model)
        if nearest_enemy_distance is not None:
            # Penalty for being too far
            if nearest_enemy_distance > agent.attack_range * 1.5:
                reward += self.config['distance_penalty'] * nearest_enemy_distance

        # 6. Team rewards (cooperative behavior)
        team_kills = action_result.get('team_kills', 0)
        if team_kills > 0:
            reward += self.config['team_kill_reward'] * team_kills * 0.5

        # 7. Battle outcome
        if not model.running:
            if self._check_victory(agent, model):
                reward += self.config['win_reward']
            else:
                reward += self.config['lose_penalty']

        return reward

    def calculate_shaped_reward(self, agent, model, prev_state, curr_state):
        """
        Calculate potential-based reward shaping

        Args:
            agent: The agent
            model: The simulation model
            prev_state: Previous agent state
            curr_state: Current agent state

        Returns:
            float: Shaped reward
        """
        gamma = 0.99  # Discount factor

        # Potential function: based on tactical advantage
        prev_potential = self._calculate_potential(agent, model, prev_state)
        curr_potential = self._calculate_potential(agent, model, curr_state)

        # Shaped reward: F(s,a,s') = γ * Φ(s') - Φ(s)
        shaped_reward = gamma * curr_potential - prev_potential

        return shaped_reward

    def _calculate_potential(self, agent, model, state):
        """Calculate potential function for reward shaping"""
        potential = 0.0

        # HP advantage
        allies_hp = sum(a.hp for a in model.agents if a.side == agent.side and a.is_alive)
        enemies_hp = sum(a.hp for a in model.agents if a.side != agent.side and a.is_alive)

        if enemies_hp > 0:
            hp_ratio = allies_hp / (allies_hp + enemies_hp)
            potential += hp_ratio * 10.0

        # Unit count advantage
        allies_count = sum(1 for a in model.agents if a.side == agent.side and a.is_alive)
        enemies_count = sum(1 for a in model.agents if a.side != agent.side and a.is_alive)

        if enemies_count > 0:
            count_ratio = allies_count / (allies_count + enemies_count)
            potential += count_ratio * 5.0

        # Agent's own HP
        if agent.is_alive:
            potential += (agent.hp / agent.max_hp) * 3.0

        return potential

    def _count_enemies_in_range(self, agent, model):
        """Count enemies within attack range"""
        count = 0
        for enemy in model.agents:
            if enemy.side != agent.side and enemy.is_alive:
                distance = agent.calculate_distance(enemy.pos)
                if distance <= agent.attack_range:
                    count += 1
        return count

    def _get_nearest_enemy_distance(self, agent, model):
        """Get distance to nearest enemy"""
        enemies = [a for a in model.agents
                  if a.side != agent.side and a.is_alive]

        if not enemies:
            return None

        distances = [agent.calculate_distance(e.pos) for e in enemies]
        return min(distances)

    def _check_victory(self, agent, model):
        """Check if agent's side won"""
        enemies_alive = any(a.side != agent.side and a.is_alive
                          for a in model.agents)
        allies_alive = any(a.side == agent.side and a.is_alive
                         for a in model.agents)

        return allies_alive and not enemies_alive

    def get_info_dict(self, agent, model):
        """
        Get additional info for logging/debugging

        Args:
            agent: The agent
            model: The simulation model

        Returns:
            dict: Info dictionary
        """
        return {
            'hp': agent.hp,
            'hp_percent': agent.hp / agent.max_hp if agent.max_hp > 0 else 0,
            'kills': agent.kills,
            'shots_fired': agent.shots_fired,
            'hits_landed': agent.hits_landed,
            'accuracy': agent.hits_landed / agent.shots_fired if agent.shots_fired > 0 else 0,
            'is_alive': agent.is_alive,
            'enemies_in_range': self._count_enemies_in_range(agent, model),
            'nearest_enemy_distance': self._get_nearest_enemy_distance(agent, model),
            'position': agent.pos
        }
