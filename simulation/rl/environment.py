"""
Gymnasium environment wrapper for combat simulation
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from copy import deepcopy

from ..model import CombatSimulation
from .observation import ObservationBuilder
from .actions import ActionSpace
from .rewards import RewardCalculator


class CombatRLEnvironment(gym.Env):
    """
    Gymnasium environment for combat simulation with RL agents

    This environment wraps the combat simulation and provides a standard
    Gym interface for training RL agents.
    """

    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 4}

    def __init__(self, objects_file='data/objects.xlsx', rules_file='data/sets.xlsx',
                 controlled_side='A', max_steps=1000):
        """
        Initialize the environment

        Args:
            objects_file: Path to objects Excel file
            rules_file: Path to rules Excel file
            controlled_side: Which side is controlled by RL ('A' or 'B')
            max_steps: Maximum steps per episode
        """
        super().__init__()

        self.objects_file = objects_file
        self.rules_file = rules_file
        self.controlled_side = controlled_side
        self.max_steps = max_steps

        # Initialize components
        self.observation_builder = ObservationBuilder(max_enemies=20, max_allies=20)
        self.action_space_handler = ActionSpace()
        self.reward_calculator = RewardCalculator()

        # Gym spaces (for single agent - will extend to multi-agent later)
        self.observation_space = self.observation_builder.get_observation_space()
        self.action_space = self.action_space_handler.get_action_space()

        # Simulation instance
        self.simulation = None
        self.current_step = 0

        # Tracking
        self.episode_rewards = []
        self.episode_info = []

        # Store previous state for reward shaping
        self.prev_agent_states = {}

    def reset(self, seed=None, options=None):
        """
        Reset the environment

        Args:
            seed: Random seed
            options: Additional options

        Returns:
            observation, info
        """
        super().reset(seed=seed)

        # Create new simulation
        self.simulation = CombatSimulation(
            objects_file=self.objects_file,
            rules_file=self.rules_file
        )

        self.current_step = 0
        self.episode_rewards = []
        self.episode_info = []
        self.prev_agent_states = {}

        # Get initial observation (for the first controlled agent)
        controlled_agent = self._get_controlled_agent()
        observation = self.observation_builder.build_observation(
            controlled_agent, self.simulation
        )

        info = self.reward_calculator.get_info_dict(controlled_agent, self.simulation)

        return observation, info

    def step(self, action):
        """
        Execute one step in the environment

        Args:
            action: Action to take (int)

        Returns:
            observation, reward, terminated, truncated, info
        """
        self.current_step += 1

        # Get controlled agent
        controlled_agent = self._get_controlled_agent()

        if controlled_agent is None or not controlled_agent.is_alive:
            # Agent is dead, return terminal state
            observation = np.zeros(self.observation_space.shape)
            reward = self.reward_calculator.config['death_penalty']
            terminated = True
            truncated = False
            info = {'reason': 'agent_dead'}
            return observation, reward, terminated, truncated, info

        # Store previous state
        prev_hp = controlled_agent.hp

        # Execute action
        action_result = self._execute_action(controlled_agent, action)

        # Execute step for other agents (opponent uses scripted AI)
        self._step_other_agents(controlled_agent)

        # Calculate reward
        reward = self.reward_calculator.calculate_reward(
            controlled_agent, self.simulation, action_result
        )

        # Get new observation
        observation = self.observation_builder.build_observation(
            controlled_agent, self.simulation
        )

        # Check termination
        terminated = not self.simulation.running or not controlled_agent.is_alive
        truncated = self.current_step >= self.max_steps

        # Get info
        info = self.reward_calculator.get_info_dict(controlled_agent, self.simulation)
        info['action'] = action
        info['action_name'] = self.action_space_handler.action_to_string(action)
        info['step'] = self.current_step
        info['damage_taken'] = prev_hp - controlled_agent.hp

        # Track episode data
        self.episode_rewards.append(reward)
        self.episode_info.append(info)

        # Increment simulation step
        self.simulation.step_count += 1

        return observation, reward, terminated, truncated, info

    def _get_controlled_agent(self):
        """Get the first alive agent on the controlled side"""
        for agent in self.simulation.agents:
            if agent.side == self.controlled_side and agent.is_alive:
                return agent
        return None

    def _execute_action(self, agent, action):
        """
        Execute action and return result

        Args:
            agent: The agent
            action: Action index

        Returns:
            dict: Action result
        """
        result = {
            'attacked': False,
            'hit': False,
            'killed': False,
            'damage_dealt': 0,
            'damage_taken': 0
        }

        # Store state before action
        prev_shots = agent.shots_fired
        prev_hits = agent.hits_landed
        prev_kills = agent.kills

        # Execute action
        success = self.action_space_handler.execute_action(agent, action, self.simulation)

        # Check if attacked
        if agent.shots_fired > prev_shots:
            result['attacked'] = True

            # Check if hit
            if agent.hits_landed > prev_hits:
                result['hit'] = True

                # Check if killed
                if agent.kills > prev_kills:
                    result['killed'] = True

        return result

    def _step_other_agents(self, controlled_agent):
        """Execute step for non-controlled agents"""
        # Shuffle agents
        agents_list = list(self.simulation.agents)
        self.simulation.random.shuffle(agents_list)

        for agent in agents_list:
            # Skip controlled agent
            if agent.unit_id == controlled_agent.unit_id:
                continue

            # Skip dead agents
            if not agent.is_alive:
                continue

            # Execute default AI behavior
            agent.step()

        # Check battle end condition
        side_a_alive = any(a.is_alive and a.side == 'A' for a in self.simulation.agents)
        side_b_alive = any(a.is_alive and a.side == 'B' for a in self.simulation.agents)

        if not side_a_alive or not side_b_alive:
            self.simulation.running = False

    def render(self, mode='human'):
        """
        Render the environment

        Args:
            mode: Render mode

        Returns:
            None or rgb array
        """
        if mode == 'human':
            # Print state to console
            self.simulation.display_status()
        elif mode == 'rgb_array':
            # Would need to implement visual rendering
            # For now, return None
            return None

    def close(self):
        """Clean up environment"""
        self.simulation = None

    def get_episode_statistics(self):
        """Get statistics for the completed episode"""
        if not self.episode_rewards:
            return {}

        return {
            'total_reward': sum(self.episode_rewards),
            'mean_reward': np.mean(self.episode_rewards),
            'episode_length': len(self.episode_rewards),
            'final_info': self.episode_info[-1] if self.episode_info else {}
        }


class MultiAgentCombatEnvironment(CombatRLEnvironment):
    """
    Multi-agent version where all units on one side are controlled by RL

    This is more complex but allows training coordinated behaviors
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Override spaces for multi-agent
        # Each agent has same obs/action space
        # We'll return dict of observations

    def reset(self, seed=None, options=None):
        """Reset and return observations for all controlled agents"""
        super().reset(seed=seed, options=options)

        observations = {}
        infos = {}

        for agent in self.simulation.agents:
            if agent.side == self.controlled_side and agent.is_alive:
                obs = self.observation_builder.build_observation(agent, self.simulation)
                info = self.reward_calculator.get_info_dict(agent, self.simulation)
                observations[agent.unit_id] = obs
                infos[agent.unit_id] = info

        return observations, infos

    def step(self, actions):
        """
        Execute actions for all controlled agents

        Args:
            actions: Dict mapping agent_id -> action

        Returns:
            observations, rewards, terminateds, truncateds, infos (all dicts)
        """
        self.current_step += 1

        observations = {}
        rewards = {}
        terminateds = {}
        truncateds = {}
        infos = {}

        # Execute actions for all controlled agents
        for agent in self.simulation.agents:
            if agent.side == self.controlled_side and agent.is_alive:
                action = actions.get(agent.unit_id, 8)  # Default: stay

                prev_hp = agent.hp
                action_result = self._execute_action(agent, action)

                reward = self.reward_calculator.calculate_reward(
                    agent, self.simulation, action_result
                )

                rewards[agent.unit_id] = reward

        # Step other agents
        self._step_other_agents_multi()

        # Get observations for all controlled agents
        for agent in self.simulation.agents:
            if agent.side == self.controlled_side:
                if agent.is_alive:
                    obs = self.observation_builder.build_observation(agent, self.simulation)
                    observations[agent.unit_id] = obs
                    terminateds[agent.unit_id] = False
                else:
                    observations[agent.unit_id] = np.zeros(self.observation_space.shape)
                    terminateds[agent.unit_id] = True

                truncateds[agent.unit_id] = self.current_step >= self.max_steps
                infos[agent.unit_id] = self.reward_calculator.get_info_dict(
                    agent, self.simulation
                )

        self.simulation.step_count += 1

        return observations, rewards, terminateds, truncateds, infos

    def _step_other_agents_multi(self):
        """Execute step for opponent agents"""
        agents_list = list(self.simulation.agents)
        self.simulation.random.shuffle(agents_list)

        for agent in agents_list:
            if agent.side != self.controlled_side and agent.is_alive:
                agent.step()

        # Check battle end
        side_a_alive = any(a.is_alive and a.side == 'A' for a in self.simulation.agents)
        side_b_alive = any(a.is_alive and a.side == 'B' for a in self.simulation.agents)

        if not side_a_alive or not side_b_alive:
            self.simulation.running = False
