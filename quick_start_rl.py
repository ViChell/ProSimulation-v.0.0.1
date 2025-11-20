"""
Quick start script for RL training

This is a simplified example to quickly understand how RL training works
"""

import numpy as np
from simulation.rl.environment import CombatRLEnvironment
from stable_baselines3 import PPO
import os


def demo_environment():
    """
    Демонстрація роботи середовища
    """
    print("="*60)
    print("ДЕМОНСТРАЦІЯ RL СЕРЕДОВИЩА")
    print("="*60)

    # Створюємо середовище
    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=100
    )

    print(f"\n1. Простір спостережень: {env.observation_space.shape}")
    print(f"   - Це вектор з {env.observation_space.shape[0]} чисел")
    print(f"   - Містить інформацію про агента, ворогів та союзників")

    print(f"\n2. Простір дій: {env.action_space.n} дій")
    print("   Дії:")
    for i in range(13):
        print(f"   - {i}: {env.action_space_handler.action_to_string(i)}")

    # Скидаємо середовище
    obs, info = env.reset()
    print(f"\n3. Початковий стан:")
    print(f"   - HP: {info['hp']:.1f}/{info['hp'] * (1/info['hp_percent']) if info['hp_percent'] > 0 else 0:.1f}")
    print(f"   - Позиція: {info['position']}")
    print(f"   - Вороги в радіусі: {info['enemies_in_range']}")

    # Виконуємо кілька випадкових дій
    print(f"\n4. Виконання дій (випадкові):")
    for step in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        print(f"   Крок {step+1}:")
        print(f"     - Дія: {env.action_space_handler.action_to_string(action)}")
        print(f"     - Винагорода: {reward:.2f}")
        print(f"     - HP: {info['hp']:.1f} ({info['hp_percent']:.1f}%)")
        print(f"     - Живий: {info['is_alive']}")

        if terminated or truncated:
            print(f"     - Епізод закінчено!")
            break

    env.close()
    print("\n" + "="*60)


def train_simple():
    """
    Просте тренування на малій кількості кроків
    """
    print("\n" + "="*60)
    print("ПРОСТЕ ТРЕНУВАННЯ (10,000 кроків)")
    print("="*60)

    # Створюємо середовище
    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=200
    )

    print("\nСтворення PPO моделі...")

    # Створюємо модель PPO
    model = PPO(
        'MlpPolicy',
        env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=5,
        verbose=1
    )

    print("\nПочинаємо тренування...")
    print("(Це займе кілька хвилин)")

    try:
        # Тренуємо
        model.learn(total_timesteps=10000, progress_bar=True)

        # Зберігаємо
        os.makedirs('models', exist_ok=True)
        model_path = 'models/quick_start_model'
        model.save(model_path)
        print(f"\nМодель збережено: {model_path}.zip")

        # Тестуємо
        print("\n" + "="*60)
        print("ТЕСТУВАННЯ НАВЧЕНОЇ МОДЕЛІ")
        print("="*60)

        test_trained_model(model, env, n_episodes=3)

    except KeyboardInterrupt:
        print("\nТренування перервано користувачем")

    env.close()


def test_trained_model(model, env, n_episodes=3):
    """
    Тестування навченої моделі

    Args:
        model: Навчена модель
        env: Середовище
        n_episodes: Кількість епізодів для тесту
    """
    rewards = []
    lengths = []

    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        step = 0
        done = False

        print(f"\nЕпізод {episode + 1}:")

        while not done:
            # Модель обирає дію
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)

            done = terminated or truncated
            episode_reward += reward
            step += 1

            # Виводимо кожен 20-й крок
            if step % 20 == 0 or done:
                print(f"  Крок {step}: HP={info['hp']:.1f}, "
                      f"Вбивства={info['kills']}, "
                      f"Влучень={info['hits_landed']}/{info['shots_fired']}")

        rewards.append(episode_reward)
        lengths.append(step)

        print(f"  Результат: винагорода={episode_reward:.2f}, "
              f"кроків={step}, живий={info['is_alive']}")

    print(f"\n{'='*60}")
    print("ПІДСУМОК:")
    print(f"  Середня винагорода: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
    print(f"  Середня довжина: {np.mean(lengths):.1f}")
    print(f"{'='*60}\n")


def compare_random_vs_trained():
    """
    Порівняння випадкового агента з навченим
    """
    print("\n" + "="*60)
    print("ПОРІВНЯННЯ: ВИПАДКОВИЙ vs НАВЧЕНИЙ")
    print("="*60)

    env = CombatRLEnvironment(
        objects_file='data/objects.xlsx',
        rules_file='data/sets.xlsx',
        controlled_side='A',
        max_steps=200
    )

    # 1. Випадковий агент
    print("\n1. ВИПАДКОВИЙ АГЕНТ (3 епізоди):")
    random_rewards = []
    for i in range(3):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        while not done:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            episode_reward += reward
        random_rewards.append(episode_reward)
        print(f"   Епізод {i+1}: {episode_reward:.2f}")

    print(f"   Середня винагорода: {np.mean(random_rewards):.2f}")

    # 2. Навчений агент (якщо існує)
    model_path = 'models/quick_start_model.zip'
    if os.path.exists(model_path):
        print("\n2. НАВЧЕНИЙ АГЕНТ (3 епізоди):")
        model = PPO.load(model_path)

        trained_rewards = []
        for i in range(3):
            obs, info = env.reset()
            episode_reward = 0
            done = False
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                episode_reward += reward
            trained_rewards.append(episode_reward)
            print(f"   Епізод {i+1}: {episode_reward:.2f}")

        print(f"   Середня винагорода: {np.mean(trained_rewards):.2f}")

        print(f"\n{'='*60}")
        print("ПОРІВНЯННЯ:")
        print(f"  Випадковий: {np.mean(random_rewards):.2f}")
        print(f"  Навчений:   {np.mean(trained_rewards):.2f}")
        improvement = ((np.mean(trained_rewards) - np.mean(random_rewards)) /
                      abs(np.mean(random_rewards)) * 100 if np.mean(random_rewards) != 0 else 0)
        print(f"  Покращення: {improvement:+.1f}%")
        print(f"{'='*60}\n")
    else:
        print("\n2. Навчена модель не знайдена")
        print(f"   Запустіть спочатку train_simple() щоб створити модель")

    env.close()


def main_menu():
    """
    Головне меню
    """
    while True:
        print("\n" + "="*60)
        print("RL QUICK START - ГОЛОВНЕ МЕНЮ")
        print("="*60)
        print("1. Демонстрація середовища")
        print("2. Просте тренування (10,000 кроків)")
        print("3. Порівняння випадковий vs навчений")
        print("4. Вихід")
        print("="*60)

        choice = input("Виберіть опцію (1-4): ").strip()

        if choice == '1':
            demo_environment()
        elif choice == '2':
            train_simple()
        elif choice == '3':
            compare_random_vs_trained()
        elif choice == '4':
            print("\nДо побачення!")
            break
        else:
            print("\nНевірний вибір, спробуйте ще раз")


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           COMBAT SIMULATION - RL QUICK START            ║
    ║                                                          ║
    ║  Простий приклад для розуміння навчання з підкріпленням ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    main_menu()
