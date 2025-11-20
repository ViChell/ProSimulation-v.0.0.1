"""
Test script to verify RL setup is working correctly
"""

import sys
import traceback
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")

    packages = {
        'gymnasium': 'gymnasium',
        'stable_baselines3': 'stable-baselines3',
        'torch': 'torch',
        'tensorboard': 'tensorboard',
        'numpy': 'numpy',
        'pandas': 'pandas'
    }

    failed = []

    for package, install_name in packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - not installed")
            failed.append(install_name)

    if failed:
        print(f"\nTo install missing packages:")
        print(f"pip install {' '.join(failed)}")
        return False

    return True


def test_rl_modules():
    """Test if RL modules are correctly structured"""
    print("\nTesting RL modules...")

    modules = [
        'simulation.rl.environment',
        'simulation.rl.observation',
        'simulation.rl.actions',
        'simulation.rl.rewards',
        'simulation.rl.rl_agent',
        'simulation.rl.config'
    ]

    failed = []

    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - {str(e)}")
            failed.append(module)

    if failed:
        print(f"\nFailed to import: {', '.join(failed)}")
        return False

    return True


def test_environment_creation():
    """Test if environment can be created"""
    print("\nTesting environment creation...")

    try:
        from simulation.rl.environment import CombatRLEnvironment

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=100
        )

        print(f"  ✓ Environment created")
        print(f"    - Observation space: {env.observation_space.shape}")
        print(f"    - Action space: {env.action_space.n} discrete actions")

        env.close()
        return True

    except Exception as e:
        print(f"  ✗ Failed to create environment")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def test_environment_reset():
    """Test if environment can be reset"""
    print("\nTesting environment reset...")

    try:
        from simulation.rl.environment import CombatRLEnvironment

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=100
        )

        obs, info = env.reset()

        print(f"  ✓ Environment reset successful")
        print(f"    - Observation shape: {obs.shape}")
        print(f"    - Agent HP: {info['hp']:.1f}")
        print(f"    - Agent position: {info['position']}")

        env.close()
        return True

    except Exception as e:
        print(f"  ✗ Failed to reset environment")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def test_environment_step():
    """Test if environment can execute steps"""
    print("\nTesting environment step...")

    try:
        from simulation.rl.environment import CombatRLEnvironment

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=100
        )

        obs, info = env.reset()

        # Take 5 random actions
        for i in range(5):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            print(f"  Step {i+1}: action={action}, reward={reward:.2f}, "
                  f"hp={info['hp']:.1f}, alive={info['is_alive']}")

            if terminated or truncated:
                print(f"    Episode ended")
                break

        print(f"  ✓ Environment step successful")

        env.close()
        return True

    except Exception as e:
        print(f"  ✗ Failed to step environment")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def test_ppo_creation():
    """Test if PPO model can be created"""
    print("\nTesting PPO model creation...")

    try:
        from simulation.rl.environment import CombatRLEnvironment
        from stable_baselines3 import PPO

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=100
        )

        model = PPO('MlpPolicy', env, verbose=0)

        print(f"  ✓ PPO model created successfully")
        print(f"    - Policy: MlpPolicy")
        print(f"    - Algorithm: PPO")

        env.close()
        return True

    except Exception as e:
        print(f"  ✗ Failed to create PPO model")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def test_quick_training():
    """Test if quick training works"""
    print("\nTesting quick training (100 steps)...")

    try:
        from simulation.rl.environment import CombatRLEnvironment
        from stable_baselines3 import PPO

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=50
        )

        model = PPO('MlpPolicy', env, verbose=0)
        model.learn(total_timesteps=100, progress_bar=False)

        print(f"  ✓ Quick training successful")

        # Test prediction
        obs, info = env.reset()
        action, _states = model.predict(obs)

        print(f"  ✓ Model prediction works (action={action})")

        env.close()
        return True

    except Exception as e:
        print(f"  ✗ Failed quick training")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def test_config():
    """Test configuration module"""
    print("\nTesting configuration module...")

    try:
        from simulation.rl.config import get_config

        configs = ['default', 'fast', 'quality', 'multi_agent']

        for config_name in configs:
            config = get_config(config_name)
            print(f"  ✓ Config '{config_name}' loaded")

        return True

    except Exception as e:
        print(f"  ✗ Failed to load configs")
        print(f"    Error: {str(e)}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("RL SETUP TEST SUITE")
    print("="*60)

    tests = [
        ("Import test", test_imports),
        ("RL modules test", test_rl_modules),
        ("Environment creation", test_environment_creation),
        ("Environment reset", test_environment_reset),
        ("Environment step", test_environment_step),
        ("PPO creation", test_ppo_creation),
        ("Quick training", test_quick_training),
        ("Configuration", test_config)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
        print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! RL setup is ready.")
        print("\nNext steps:")
        print("1. Run: python quick_start_rl.py")
        print("2. Or run: python train_rl.py --mode test")
        print("3. For full training: python train_rl.py --mode train")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Make sure data files exist: data/objects.xlsx, data/sets.xlsx")
        print("3. Check Python version (requires 3.8+)")

    print("="*60)

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
