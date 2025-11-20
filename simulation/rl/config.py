"""
Configuration for RL training
"""


# Observation space configuration
OBSERVATION_CONFIG = {
    'max_enemies': 20,           # Maximum number of enemies to observe
    'max_allies': 20,            # Maximum number of allies to observe
    'self_state_dim': 10,        # Dimensions for self state
    'enemy_feature_dim': 8,      # Features per enemy
    'ally_feature_dim': 8        # Features per ally
}


# Reward configuration
REWARD_CONFIG = {
    # Combat rewards
    'kill_reward': 10.0,           # Reward for killing an enemy
    'hit_reward': 1.0,             # Reward for hitting an enemy
    'miss_penalty': -0.1,          # Penalty for missing a shot

    # Survival
    'death_penalty': -50.0,        # Penalty for dying
    'survival_reward': 0.1,        # Reward per step survived
    'damage_taken_penalty': -2.0,  # Penalty per HP lost (scaled by max_hp)

    # Tactical positioning
    'in_range_reward': 0.5,        # Reward for having enemies in attack range
    'distance_penalty': -0.01,     # Penalty for being too far from enemies
    'retreat_penalty': -0.2,       # Small penalty for retreating

    # Team coordination
    'team_kill_reward': 5.0,       # Shared reward when teammate kills

    # Battle outcome
    'win_reward': 100.0,           # Bonus for winning the battle
    'lose_penalty': -100.0         # Penalty for losing the battle
}


# PPO hyperparameters
PPO_CONFIG = {
    'learning_rate': 3e-4,         # Learning rate
    'n_steps': 2048,               # Number of steps per rollout
    'batch_size': 64,              # Minibatch size
    'n_epochs': 10,                # Number of epochs per update
    'gamma': 0.99,                 # Discount factor
    'gae_lambda': 0.95,            # GAE lambda
    'clip_range': 0.2,             # PPO clip range
    'clip_range_vf': None,         # Value function clip range
    'ent_coef': 0.01,              # Entropy coefficient
    'vf_coef': 0.5,                # Value function coefficient
    'max_grad_norm': 0.5,          # Maximum gradient norm
    'target_kl': None              # Target KL divergence
}


# Training configuration
TRAINING_CONFIG = {
    'total_timesteps': 100000,     # Total training timesteps
    'n_envs': 4,                   # Number of parallel environments
    'max_episode_steps': 1000,     # Maximum steps per episode
    'eval_freq': 10000,            # Evaluation frequency
    'save_freq': 10000,            # Model save frequency
    'n_eval_episodes': 5,          # Number of evaluation episodes
    'log_interval': 10             # Logging interval
}


# Environment configuration
ENV_CONFIG = {
    'controlled_side': 'A',        # Which side is controlled by RL ('A' or 'B')
    'max_steps': 1000,             # Maximum steps per episode
    'render_mode': None            # Render mode: None, 'human', 'rgb_array'
}


# Network architecture (for custom networks)
NETWORK_CONFIG = {
    'policy_layers': [256, 256],   # Hidden layers for policy network
    'value_layers': [256, 256],    # Hidden layers for value network
    'activation': 'tanh'           # Activation function: 'tanh', 'relu'
}


# Multi-agent configuration
MULTI_AGENT_CONFIG = {
    'enabled': False,              # Enable multi-agent training
    'shared_policy': True,         # Share policy between agents
    'communication': False,        # Enable agent communication
    'comm_dim': 16                 # Communication message dimension
}


# Curriculum learning configuration
CURRICULUM_CONFIG = {
    'enabled': False,              # Enable curriculum learning
    'stages': [
        {'name': '1v1', 'min_units_per_side': 1, 'max_units_per_side': 1, 'timesteps': 50000},
        {'name': '3v3', 'min_units_per_side': 3, 'max_units_per_side': 3, 'timesteps': 100000},
        {'name': '5v5', 'min_units_per_side': 5, 'max_units_per_side': 5, 'timesteps': 200000},
        {'name': 'full', 'min_units_per_side': 1, 'max_units_per_side': 20, 'timesteps': 300000}
    ]
}


# Logging configuration
LOGGING_CONFIG = {
    'tensorboard': True,           # Enable TensorBoard logging
    'wandb': False,                # Enable Weights & Biases logging
    'wandb_project': 'combat-sim', # W&B project name
    'log_dir': 'logs',             # Log directory
    'video_freq': 50000,           # Video recording frequency (0=disabled)
    'video_length': 100            # Video length in steps
}


def get_config(config_name='default'):
    """
    Get configuration preset

    Args:
        config_name: Name of configuration preset
            - 'default': Standard configuration
            - 'fast': Quick training for testing
            - 'quality': High-quality training
            - 'multi_agent': Multi-agent training

    Returns:
        dict: Configuration dictionary
    """
    if config_name == 'default':
        return {
            'observation': OBSERVATION_CONFIG,
            'reward': REWARD_CONFIG,
            'ppo': PPO_CONFIG,
            'training': TRAINING_CONFIG,
            'env': ENV_CONFIG,
            'network': NETWORK_CONFIG,
            'multi_agent': MULTI_AGENT_CONFIG,
            'curriculum': CURRICULUM_CONFIG,
            'logging': LOGGING_CONFIG
        }

    elif config_name == 'fast':
        # Fast training for testing
        fast_training = TRAINING_CONFIG.copy()
        fast_training['total_timesteps'] = 10000
        fast_training['n_envs'] = 2
        fast_training['eval_freq'] = 5000
        fast_training['save_freq'] = 5000

        fast_ppo = PPO_CONFIG.copy()
        fast_ppo['n_steps'] = 512
        fast_ppo['n_epochs'] = 5

        return {
            'observation': OBSERVATION_CONFIG,
            'reward': REWARD_CONFIG,
            'ppo': fast_ppo,
            'training': fast_training,
            'env': ENV_CONFIG,
            'network': NETWORK_CONFIG,
            'multi_agent': MULTI_AGENT_CONFIG,
            'curriculum': CURRICULUM_CONFIG,
            'logging': LOGGING_CONFIG
        }

    elif config_name == 'quality':
        # High-quality training
        quality_training = TRAINING_CONFIG.copy()
        quality_training['total_timesteps'] = 1000000
        quality_training['n_envs'] = 8
        quality_training['eval_freq'] = 50000

        quality_ppo = PPO_CONFIG.copy()
        quality_ppo['n_steps'] = 4096
        quality_ppo['batch_size'] = 128
        quality_ppo['n_epochs'] = 15

        return {
            'observation': OBSERVATION_CONFIG,
            'reward': REWARD_CONFIG,
            'ppo': quality_ppo,
            'training': quality_training,
            'env': ENV_CONFIG,
            'network': NETWORK_CONFIG,
            'multi_agent': MULTI_AGENT_CONFIG,
            'curriculum': CURRICULUM_CONFIG,
            'logging': LOGGING_CONFIG
        }

    elif config_name == 'multi_agent':
        # Multi-agent configuration
        ma_config = MULTI_AGENT_CONFIG.copy()
        ma_config['enabled'] = True

        ma_training = TRAINING_CONFIG.copy()
        ma_training['total_timesteps'] = 500000

        return {
            'observation': OBSERVATION_CONFIG,
            'reward': REWARD_CONFIG,
            'ppo': PPO_CONFIG,
            'training': ma_training,
            'env': ENV_CONFIG,
            'network': NETWORK_CONFIG,
            'multi_agent': ma_config,
            'curriculum': CURRICULUM_CONFIG,
            'logging': LOGGING_CONFIG
        }

    else:
        raise ValueError(f"Unknown config name: {config_name}")


def print_config(config):
    """Print configuration in a readable format"""
    print("\n" + "="*60)
    print("TRAINING CONFIGURATION")
    print("="*60)

    for category, params in config.items():
        print(f"\n{category.upper()}:")
        for key, value in params.items():
            print(f"  {key}: {value}")

    print("\n" + "="*60 + "\n")
