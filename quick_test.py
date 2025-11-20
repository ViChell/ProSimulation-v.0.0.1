"""Quick test to verify basic RL setup"""

print("="*60)
print("QUICK RL TEST")
print("="*60)

# Test 1: Import gymnasium
print("\n1. Testing gymnasium...")
try:
    import gymnasium as gym
    print("   [OK] gymnasium imported")
except Exception as e:
    print(f"   [FAIL] {e}")
    exit(1)

# Test 2: Import stable-baselines3
print("\n2. Testing stable-baselines3...")
try:
    from stable_baselines3 import PPO
    print("   [OK] stable-baselines3 imported")
except Exception as e:
    print(f"   [FAIL] {e}")
    exit(1)

# Test 3: Import torch
print("\n3. Testing torch...")
try:
    import torch
    print("   [OK] torch imported")
    print(f"   PyTorch version: {torch.__version__}")
except Exception as e:
    print(f"   [FAIL] {e}")
    exit(1)

# Test 4: Import RL modules
print("\n4. Testing RL modules...")
try:
    from simulation.rl import CombatRLEnvironment
    print("   [OK] CombatRLEnvironment imported")
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Create environment
print("\n5. Creating environment...")
try:
    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=100
    )
    print("   [OK] Environment created")
    print(f"   Observation space: {env.observation_space.shape}")
    print(f"   Action space: {env.action_space.n} actions")
    env.close()
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Reset environment
print("\n6. Testing environment reset...")
try:
    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=100
    )
    obs, info = env.reset()
    print("   [OK] Environment reset successful")
    print(f"   Agent HP: {info['hp']:.1f}")
    env.close()
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nRL setup is working correctly!")
print("\nNext steps:")
print("  python quick_start_rl.py    - Interactive demo")
print("  python train_rl.py --mode test - Test environment with random actions")
print("="*60)
