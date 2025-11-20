"""
Training script for RL agents in combat simulation

This script trains an RL agent using Stable-Baselines3 PPO algorithm
"""

import os
import argparse
from datetime import datetime

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy

from simulation.rl.environment import CombatRLEnvironment


def make_env(objects_file, rules_file, controlled_side='A', max_steps=1000, rank=0):
    """
    Create a single environment instance

    Args:
        objects_file: Path to objects file
        rules_file: Path to rules file
        controlled_side: Which side to control
        max_steps: Max steps per episode
        rank: Process rank (for parallel training)

    Returns:
        Function that creates environment
    """
    def _init():
        env = CombatRLEnvironment(
            objects_file=objects_file,
            rules_file=rules_file,
            controlled_side=controlled_side,
            max_steps=max_steps
        )
        env = Monitor(env)
        return env

    return _init


def train_ppo(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A',
    total_timesteps=100000,
    n_envs=4,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    max_steps=1000,
    save_dir='models',
    eval_freq=10000,
    save_freq=10000
):
    """
    Train PPO agent

    Args:
        objects_file: Path to objects Excel file
        rules_file: Path to rules Excel file
        controlled_side: Which side is controlled by RL ('A' or 'B')
        total_timesteps: Total training timesteps
        n_envs: Number of parallel environments
        learning_rate: Learning rate
        n_steps: Steps per rollout
        batch_size: Minibatch size
        n_epochs: Number of epochs per update
        gamma: Discount factor
        gae_lambda: GAE lambda
        clip_range: PPO clip range
        ent_coef: Entropy coefficient
        max_steps: Max steps per episode
        save_dir: Directory to save models
        eval_freq: Evaluation frequency
        save_freq: Checkpoint save frequency

    Returns:
        Trained model
    """
    # Create directories
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = os.path.join(save_dir, f'ppo_combat_{timestamp}')
    os.makedirs(model_dir, exist_ok=True)

    print(f"Training PPO agent...")
    print(f"Controlled side: {controlled_side}")
    print(f"Total timesteps: {total_timesteps}")
    print(f"Number of environments: {n_envs}")
    print(f"Model directory: {model_dir}")

    # Create vectorized environments
    if n_envs > 1:
        env = SubprocVecEnv([
            make_env(objects_file, rules_file, controlled_side, max_steps, i)
            for i in range(n_envs)
        ])
    else:
        env = DummyVecEnv([
            make_env(objects_file, rules_file, controlled_side, max_steps, 0)
        ])

    # Create evaluation environment
    eval_env = DummyVecEnv([
        make_env(objects_file, rules_file, controlled_side, max_steps, 999)
    ])

    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq // n_envs,
        save_path=model_dir,
        name_prefix='ppo_combat'
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=model_dir,
        eval_freq=eval_freq // n_envs,
        n_eval_episodes=5,
        deterministic=True
    )

    # Create PPO model
    model = PPO(
        'MlpPolicy',
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        verbose=1,
        tensorboard_log=os.path.join(model_dir, 'tensorboard')
    )

    print("\nStarting training...")
    print(f"Tensorboard logs: {os.path.join(model_dir, 'tensorboard')}")
    print(f"Run: tensorboard --logdir {os.path.join(model_dir, 'tensorboard')}")

    # Train
    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")

    # Save final model
    final_model_path = os.path.join(model_dir, 'final_model')
    model.save(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")

    # Evaluate final model
    print("\nEvaluating final model...")
    mean_reward, std_reward = evaluate_policy(
        model, eval_env, n_eval_episodes=10, deterministic=True
    )
    print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

    # Cleanup
    env.close()
    eval_env.close()

    return model, model_dir


def test_environment():
    """Test the environment with random actions"""
    print("Testing environment with random actions...")

    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=100
    )

    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")

    # Run one episode
    obs, info = env.reset()
    print(f"\nInitial observation shape: {obs.shape}")
    print(f"Initial info: {info}")

    total_reward = 0
    done = False
    step = 0

    while not done and step < 20:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        done = terminated or truncated
        total_reward += reward
        step += 1

        print(f"Step {step}: action={action}, reward={reward:.2f}, "
              f"hp={info.get('hp', 0):.1f}, alive={info.get('is_alive', False)}")

    print(f"\nEpisode finished after {step} steps")
    print(f"Total reward: {total_reward:.2f}")
    print(f"Episode stats: {env.get_episode_statistics()}")

    env.close()


def load_and_test(model_path, n_episodes=5):
    """
    Load trained model and test it

    Args:
        model_path: Path to saved model
        n_episodes: Number of episodes to test
    """
    print(f"Loading model from: {model_path}")

    # Load model
    model = PPO.load(model_path)

    # Create environment
    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=1000
    )

    print(f"Testing for {n_episodes} episodes...")

    episode_rewards = []
    episode_lengths = []
    wins = 0

    for episode in range(n_episodes):
        obs, info = env.reset()
        done = False
        episode_reward = 0
        step = 0

        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            episode_reward += reward
            step += 1

        episode_rewards.append(episode_reward)
        episode_lengths.append(step)

        # Check if won
        if info.get('is_alive', False):
            wins += 1

        print(f"Episode {episode + 1}: reward={episode_reward:.2f}, "
              f"length={step}, alive={info.get('is_alive', False)}")

    print(f"\nTest Results:")
    print(f"Mean reward: {sum(episode_rewards) / len(episode_rewards):.2f}")
    print(f"Mean length: {sum(episode_lengths) / len(episode_lengths):.1f}")
    print(f"Win rate: {wins / n_episodes * 100:.1f}%")

    env.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Train RL agent for combat simulation')
    parser.add_argument('--mode', type=str, default='train',
                       choices=['train', 'test', 'test-model'],
                       help='Mode: train, test (random), or test-model (load trained)')
    parser.add_argument('--model-path', type=str, default=None,
                       help='Path to model for testing')
    parser.add_argument('--timesteps', type=int, default=100000,
                       help='Total training timesteps')
    parser.add_argument('--n-envs', type=int, default=4,
                       help='Number of parallel environments')
    parser.add_argument('--side', type=str, default='A',
                       choices=['A', 'B'],
                       help='Side to control with RL')
    parser.add_argument('--save-dir', type=str, default='models',
                       help='Directory to save models')

    args = parser.parse_args()

    if args.mode == 'test':
        # Test environment with random actions
        test_environment()

    elif args.mode == 'test-model':
        # Test trained model
        if args.model_path is None:
            print("Error: --model-path required for test-model mode")
            return
        load_and_test(args.model_path, n_episodes=5)

    elif args.mode == 'train':
        # Train model
        model, model_dir = train_ppo(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side=args.side,
            total_timesteps=args.timesteps,
            n_envs=args.n_envs,
            save_dir=args.save_dir
        )

        print(f"\nTraining complete!")
        print(f"Model saved to: {model_dir}")
        print(f"\nTo test the model, run:")
        print(f"python train_rl.py --mode test-model --model-path {os.path.join(model_dir, 'final_model.zip')}")


if __name__ == '__main__':
    main()
