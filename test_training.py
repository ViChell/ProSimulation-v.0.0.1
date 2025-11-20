"""Test quick training to verify everything works"""

print("="*60)
print("TESTING RL TRAINING")
print("="*60)

from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO
import numpy as np

# Create environment
print("\n1. Creating environment...")
env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A',
    max_steps=50
)
print("   [OK] Environment created")

# Create model
print("\n2. Creating PPO model...")
model = PPO('MlpPolicy', env, verbose=0)
print("   [OK] Model created")

# Quick training
print("\n3. Quick training (500 steps)...")
try:
    model.learn(total_timesteps=500, progress_bar=False)
    print("   [OK] Training completed")
except Exception as e:
    print(f"   [FAIL] Training failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test prediction
print("\n4. Testing prediction...")
try:
    obs, info = env.reset()

    for step in range(10):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)

        print(f"   Step {step+1}: action={action}, reward={reward:.2f}, hp={info['hp']:.1f}")

        if terminated or truncated:
            print(f"   Episode ended")
            break

    print("   [OK] Prediction works")
except Exception as e:
    print(f"   [FAIL] Prediction failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

env.close()

print("\n" + "="*60)
print("TRAINING TEST PASSED!")
print("="*60)
print("\nYou can now:")
print("  - Run full training: python train_rl.py --mode train")
print("  - Interactive demo: python quick_start_rl.py")
print("="*60)
