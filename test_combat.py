"""
Test combat with close units to see action!
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from simulation.rl import CombatRLEnvironment

print("="*80)
print("ТЕСТ БОЙОВИХ ДІЙ")
print("="*80)

# Create environment with test scenario
env = CombatRLEnvironment(
    objects_file='data/test_objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A',
    max_steps=50
)

print("\n🎮 Запуск симуляції з випадковими діями...\n")

obs, info = env.reset()

print(f"Початковий стан:")
print(f"  HP: {info['hp']:.1f}")
print(f"  Позиція: ({info['position'][0]:.3f}, {info['position'][1]:.3f})")
print(f"  Вороги в радіусі атаки: {info['enemies_in_range']}")
print(f"  Дистанція до ворога: {info['nearest_enemy_distance']:.2f} км")

print("\n" + "-"*80)
print("ХРОНОЛОГІЯ:")
print("-"*80)

for step in range(30):
    action = env.action_space.sample()

    prev_shots = info['shots_fired']
    prev_hits = info['hits_landed']
    prev_kills = info['kills']
    prev_hp = info['hp']

    obs, reward, terminated, truncated, info = env.step(action)

    new_shots = info['shots_fired'] - prev_shots
    new_hits = info['hits_landed'] - prev_hits
    new_kills = info['kills'] - prev_kills
    hp_change = info['hp'] - prev_hp

    action_names = {
        0: "⬆️  North", 1: "⬇️  South", 2: "➡️  East", 3: "⬅️  West",
        4: "↗️  NE", 5: "↖️  NW", 6: "↘️  SE", 7: "↙️  SW",
        8: "⏸️  Stay", 9: "🎯 Attack Near", 10: "🎯 Attack Weak",
        11: "🎯 Attack Strong", 12: "🏃 Retreat"
    }

    status = ""
    if new_shots > 0:
        if new_hits > 0:
            status = "💥 ВЛУЧИВ!"
            if new_kills > 0:
                status += f" ☠️  ВБИВ! (+{new_kills})"
        else:
            status = "❌ Промах"

    if hp_change < 0:
        status += f" ❤️  -{abs(hp_change):.0f} HP"

    print(f"Крок {step+1:2}: {action_names.get(action, 'Unknown'):15} | "
          f"HP: {info['hp']:5.1f} | Вороги: {info['enemies_in_range']} | "
          f"K:{info['kills']} S:{info['shots_fired']} H:{info['hits_landed']} | "
          f"{status}")

    if terminated or truncated:
        print(f"\n{'='*80}")
        print(f"БІЙ ЗАКІНЧЕНО! (Крок {step+1})")
        print(f"{'='*80}")
        break

print("\n" + "="*80)
print("ФІНАЛЬНА СТАТИСТИКА")
print("="*80)

print(f"\nРезультат:")
print(f"  Статус: {'✅ Живий' if info['is_alive'] else '💀 Загинув'}")
print(f"  HP: {info['hp']:.1f} / {info['hp']/info['hp_percent']*100 if info['hp_percent'] > 0 else 0:.1f} ({info['hp_percent']:.1f}%)")
print(f"  Вбивств: {info['kills']}")
print(f"  Пострілів: {info['shots_fired']}")
print(f"  Влучень: {info['hits_landed']}")
print(f"  Точність: {(info['hits_landed']/info['shots_fired']*100) if info['shots_fired'] > 0 else 0:.1f}%")

env.close()

print("\n" + "="*80)
print("Тепер запустіть:")
print("  python visualize_training.py  - для детальної візуалізації")
print("  python train_rl.py --mode train --timesteps 10000  - для тренування")
print("="*80)
