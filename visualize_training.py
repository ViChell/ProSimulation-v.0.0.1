"""
Visualize what's happening during training
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO
import numpy as np


def run_episode_with_visualization(env, model=None, deterministic=True):
    """
    Run one episode with detailed visualization

    Args:
        env: Environment
        model: Trained model (if None, uses random actions)
        deterministic: Use deterministic actions
    """
    obs, info = env.reset()

    print("\n" + "="*80)
    print("ПОЧАТОК ЕПІЗОДУ")
    print("="*80)

    print(f"\nПочатковий стан агента:")
    print(f"  ID: {info.get('position')}")
    print(f"  HP: {info['hp']:.1f}")
    print(f"  Позиція: ({info['position'][0]:.3f}, {info['position'][1]:.3f})")
    print(f"  Вороги в радіусі атаки: {info['enemies_in_range']}")
    print(f"  Дистанція до найближчого ворога: {info['nearest_enemy_distance']:.2f} км")

    total_reward = 0
    step = 0
    done = False

    # Statistics
    total_shots = 0
    total_hits = 0
    total_kills = 0
    actions_taken = {i: 0 for i in range(13)}
    action_names = {
        0: "Move North", 1: "Move South", 2: "Move East", 3: "Move West",
        4: "Move NE", 5: "Move NW", 6: "Move SE", 7: "Move SW",
        8: "Stay", 9: "Attack Nearest", 10: "Attack Weakest", 11: "Attack Strongest",
        12: "Retreat"
    }

    print("\n" + "-"*80)
    print("ХРОНОЛОГІЯ КРОКІВ:")
    print("-"*80)

    while not done and step < 100:
        # Get action
        if model is not None:
            action, _ = model.predict(obs, deterministic=deterministic)
            if hasattr(action, 'item'):
                action = int(action.item())
            else:
                action = int(action)
        else:
            action = env.action_space.sample()

        # Track action
        actions_taken[action] = actions_taken.get(action, 0) + 1

        # Take step
        prev_shots = info['shots_fired']
        prev_hits = info['hits_landed']
        prev_kills = info['kills']
        prev_hp = info['hp']

        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

        # Analyze what happened
        new_shots = info['shots_fired'] - prev_shots
        new_hits = info['hits_landed'] - prev_hits
        new_kills = info['kills'] - prev_kills
        hp_change = info['hp'] - prev_hp

        total_shots += new_shots
        total_hits += new_hits
        total_kills += new_kills
        total_reward += reward

        step += 1

        # Print step info
        print(f"\nКрок {step}:")
        print(f"  Дія: {action_names[action]} (#{action})")
        print(f"  Винагорода: {reward:+.3f}")

        if new_shots > 0:
            print(f"  💥 ПОСТРІЛ! {'Влучив!' if new_hits > 0 else 'Промах'}")
            if new_kills > 0:
                print(f"  ☠️  ВБИВСТВО! (+{new_kills})")

        if hp_change < 0:
            print(f"  ❤️  Отримано пошкодження: {hp_change:.1f} HP")

        print(f"  HP: {info['hp']:.1f} ({info['hp_percent']:.1f}%)")
        print(f"  Позиція: ({info['position'][0]:.3f}, {info['position'][1]:.3f})")
        print(f"  Вороги в радіусі: {info['enemies_in_range']}")
        print(f"  Статистика: {info['kills']} вбивств, {info['hits_landed']}/{info['shots_fired']} влучень")

        if done:
            print(f"\n{'='*80}")
            print(f"ЕПІЗОД ЗАВЕРШЕНО на кроці {step}")
            print(f"{'='*80}")
            if terminated:
                print(f"Причина: {'Агент загинув' if not info['is_alive'] else 'Бій закінчився'}")
            else:
                print(f"Причина: Досягнуто ліміт кроків")

    # Final statistics
    print("\n" + "="*80)
    print("СТАТИСТИКА ЕПІЗОДУ")
    print("="*80)

    print(f"\nЗагальна інформація:")
    print(f"  Кроків: {step}")
    print(f"  Загальна винагорода: {total_reward:.2f}")
    print(f"  Середня винагорода за крок: {total_reward/step if step > 0 else 0:.3f}")
    print(f"  Кінцевий стан: {'Живий ✓' if info['is_alive'] else 'Загинув ✗'}")
    print(f"  Кінцеве HP: {info['hp']:.1f} ({info['hp_percent']:.1f}%)")

    print(f"\nБойова ефективність:")
    print(f"  Вбивств: {total_kills}")
    print(f"  Пострілів: {total_shots}")
    print(f"  Влучень: {total_hits}")
    print(f"  Точність: {(total_hits/total_shots*100) if total_shots > 0 else 0:.1f}%")

    print(f"\nРозподіл дій:")
    for action, count in sorted(actions_taken.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / step * 100) if step > 0 else 0
            print(f"  {action_names[action]:20} : {count:3} разів ({percentage:5.1f}%)")

    print("="*80 + "\n")

    return total_reward, step, info


def compare_random_vs_trained(model_path=None):
    """Compare random agent vs trained agent"""

    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=200
    )

    print("\n" + "🎲"*40)
    print("ПОРІВНЯННЯ: ВИПАДКОВИЙ vs НАВЧЕНИЙ АГЕНТ")
    print("🎲"*40 + "\n")

    # Random agent
    print("\n" + "🎲 ВИПАДКОВИЙ АГЕНТ 🎲")
    random_reward, random_steps, random_info = run_episode_with_visualization(env, model=None)

    # Trained agent
    if model_path:
        print("\n" + "🤖 НАВЧЕНИЙ АГЕНТ 🤖")
        model = PPO.load(model_path)
        trained_reward, trained_steps, trained_info = run_episode_with_visualization(env, model=model)

        # Comparison
        print("\n" + "="*80)
        print("ПОРІВНЯЛЬНА ТАБЛИЦЯ")
        print("="*80)

        print(f"\n{'Метрика':<30} {'Випадковий':>15} {'Навчений':>15} {'Різниця':>15}")
        print("-"*80)

        print(f"{'Винагорода':<30} {random_reward:>15.2f} {trained_reward:>15.2f} {trained_reward-random_reward:>+15.2f}")
        print(f"{'Кроків виконано':<30} {random_steps:>15} {trained_steps:>15} {trained_steps-random_steps:>+15}")
        print(f"{'Вбивств':<30} {random_info['kills']:>15} {trained_info['kills']:>15} {trained_info['kills']-random_info['kills']:>+15}")
        print(f"{'Пострілів':<30} {random_info['shots_fired']:>15} {trained_info['shots_fired']:>15} {trained_info['shots_fired']-random_info['shots_fired']:>+15}")
        print(f"{'Влучень':<30} {random_info['hits_landed']:>15} {trained_info['hits_landed']:>15} {trained_info['hits_landed']-random_info['hits_landed']:>+15}")

        acc_random = (random_info['hits_landed']/random_info['shots_fired']*100) if random_info['shots_fired'] > 0 else 0
        acc_trained = (trained_info['hits_landed']/trained_info['shots_fired']*100) if trained_info['shots_fired'] > 0 else 0
        print(f"{'Точність (%)':<30} {acc_random:>15.1f} {acc_trained:>15.1f} {acc_trained-acc_random:>+15.1f}")

        print(f"{'Кінцеве HP':<30} {random_info['hp']:>15.1f} {trained_info['hp']:>15.1f} {trained_info['hp']-random_info['hp']:>+15.1f}")
        print(f"{'Живий?':<30} {'Так' if random_info['is_alive'] else 'Ні':>15} {'Так' if trained_info['is_alive'] else 'Ні':>15}")

        print("="*80 + "\n")

    env.close()


def main():
    """Main menu"""
    print("\n" + "🔍"*40)
    print("ВІЗУАЛІЗАЦІЯ ТРЕНУВАННЯ RL")
    print("🔍"*40 + "\n")

    print("Оберіть режим:")
    print("1. Випадковий агент (детальна візуалізація)")
    print("2. Навчений агент (детальна візуалізація)")
    print("3. Порівняння випадковий vs навчений")
    print("4. Швидке тренування з візуалізацією до/після")
    print("5. Вихід")

    choice = input("\nВаш вибір (1-5): ").strip()

    if choice == '1':
        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=200
        )
        run_episode_with_visualization(env, model=None)
        env.close()

    elif choice == '2':
        import os
        import glob

        # Find latest model
        model_files = glob.glob('models/**/final_model.zip', recursive=True)
        if not model_files:
            model_files = glob.glob('models/**/best_model.zip', recursive=True)

        if not model_files:
            print("\n⚠️  Модель не знайдена!")
            print("Спочатку натренуйте модель:")
            print("  python train_rl.py --mode train --timesteps 10000")
            return

        latest_model = max(model_files, key=os.path.getctime)
        print(f"\n✓ Завантажую модель: {latest_model}")

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=200
        )
        model = PPO.load(latest_model)
        run_episode_with_visualization(env, model=model)
        env.close()

    elif choice == '3':
        import os
        import glob

        model_files = glob.glob('models/**/final_model.zip', recursive=True)
        if not model_files:
            model_files = glob.glob('models/**/best_model.zip', recursive=True)

        if model_files:
            latest_model = max(model_files, key=os.path.getctime)
            print(f"\n✓ Завантажую модель: {latest_model}")
            compare_random_vs_trained(latest_model)
        else:
            print("\n⚠️  Модель не знайдена!")
            print("Запускаю порівняння тільки з випадковим агентом...")
            compare_random_vs_trained(None)

    elif choice == '4':
        print("\n🚀 Швидке тренування з візуалізацією...")

        env = CombatRLEnvironment(
            objects_file='data/objects.xlsx',
            rules_file='data/sets.xlsx',
            controlled_side='A',
            max_steps=100
        )

        print("\n📊 ДО ТРЕНУВАННЯ:")
        model = PPO('MlpPolicy', env, verbose=0)
        run_episode_with_visualization(env, model=model)

        print("\n⏳ Тренування (5000 кроків)...")
        model.learn(total_timesteps=5000, progress_bar=True)

        print("\n📊 ПІСЛЯ ТРЕНУВАННЯ:")
        run_episode_with_visualization(env, model=model)

        env.close()

    elif choice == '5':
        print("\nДо побачення!")
    else:
        print("\n⚠️  Невірний вибір")


if __name__ == '__main__':
    main()
