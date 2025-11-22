"""
Тестовий скрипт для демонстрації автоматичного аналізу логів
Запускає коротку симуляцію та автоматично генерує звіт
"""

from simulation.model import CombatSimulation
import config

def main():
    print("="*70)
    print(" "*20 + "TEST AUTO ANALYSIS")
    print("="*70)
    print()
    print("Запуск симуляції...")
    print("Автоматичний аналіз запуститься після завершення")
    print("="*70)
    print()

    # Створити симуляцію
    sim = CombatSimulation(
        objects_file=config.OBJECTS_FILE,
        rules_file=config.RULES_FILE
    )

    # Запустити симуляцію до завершення
    max_steps = 100
    step = 0

    while sim.running and step < max_steps:
        sim.step()
        step += 1

        # Виводити прогрес кожні 10 кроків
        if step % 10 == 0:
            side_a = len([a for a in sim.agents if a.side == 'A' and a.is_alive])
            side_b = len([a for a in sim.agents if a.side == 'B' and a.is_alive])
            print(f"Step {step}: Side A={side_a} alive, Side B={side_b} alive")

    print()
    print("="*70)
    print("Симуляція завершена!")
    print(f"Всього кроків: {sim.step_count}")
    print("="*70)
    print()

    # Аналіз вже запущений автоматично в sim.step()
    # Результати збережені в logs/analysis_*.txt

    print("Перевірте файли:")
    print("  - logs/analysis_DD_MM_YYYY_HH_MM_SS.txt - детальний звіт")
    print("  - logs/combat/combat_*_analysis.json - JSON дані")
    print()


if __name__ == '__main__':
    main()
