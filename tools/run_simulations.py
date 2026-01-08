"""
Batch Simulation Runner

Запускає множинні симуляції з відстеженням прогресу та автоматичним
створенням зведеного звіту.

Usage:
    python tools/run_simulations.py
    python tools/run_simulations.py --count 20
    python tools/run_simulations.py --count 10 --config data/objects2.xlsx
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.model import CombatSimulation
from tools.consolidate_analysis import ConsolidatedAnalyzer


class SimulationBatch:
    """Керує серією симуляцій"""

    def __init__(self, count=10,
                 types_file='data/unit_types.xlsx',
                 instances_file='data/unit_instances.xlsx',
                 rules_file='data/engagement_rules.xlsx'):
        self.count = count
        self.types_file = types_file
        self.instances_file = instances_file
        self.rules_file = rules_file
        self.results = []
        self.start_time = None
        self.end_time = None

    def run(self):
        """Запустити всі симуляції"""
        print("\n" + "=" * 70)
        print(f"BATCH SIMULATION RUN - {self.count} simulations".center(70))
        print("=" * 70)
        print(f"\nUnit types:  {self.types_file}")
        print(f"Instances:   {self.instances_file}")
        print(f"Rules:       {self.rules_file}")
        print(f"Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.start_time = time.time()

        for i in range(self.count):
            self._run_single(i + 1)

        self.end_time = time.time()
        self._print_summary()
        self._run_consolidation()

    def _run_single(self, sim_number):
        """Запустити одну симуляцію"""
        print(f"\n[{sim_number}/{self.count}] Starting simulation...")

        try:
            sim = CombatSimulation(
                types_file=self.types_file,
                instances_file=self.instances_file,
                rules_file=self.rules_file
            )

            # Запустити до завершення
            step_count = 0
            while sim.running:
                sim.step()
                step_count += 1

                # Прогрес кожні 20 кроків
                if step_count % 20 == 0:
                    potential = sim.calculate_current_potential()
                    pot_a = (potential['A'] / sim.initial_potential['A'] * 100) if sim.initial_potential['A'] > 0 else 0
                    pot_b = (potential['B'] / sim.initial_potential['B'] * 100) if sim.initial_potential['B'] > 0 else 0
                    print(f"  Step {step_count}: A={pot_a:.0f}% B={pot_b:.0f}%", end='\r')

            # Визначити переможця та причину
            final_potential = sim.calculate_current_potential()
            pot_a_final = (final_potential['A'] / sim.initial_potential['A'] * 100) if sim.initial_potential['A'] > 0 else 0
            pot_b_final = (final_potential['B'] / sim.initial_potential['B'] * 100) if sim.initial_potential['B'] > 0 else 0

            side_a_alive = len([a for a in sim.agents if a.side == 'A' and a.is_alive])
            side_b_alive = len([a for a in sim.agents if a.side == 'B' and a.is_alive])

            # Визначити переможця
            if side_a_alive == 0 or pot_a_final <= 30:
                winner = 'B'
                reason = 'destruction' if side_a_alive == 0 else f'potential {pot_a_final:.0f}%'
            else:
                winner = 'A'
                reason = 'destruction' if side_b_alive == 0 else f'potential {pot_b_final:.0f}%'

            result = {
                'number': sim_number,
                'steps': sim.step_count,
                'winner': winner,
                'reason': reason,
                'potential_a': pot_a_final,
                'potential_b': pot_b_final,
                'alive_a': side_a_alive,
                'alive_b': side_b_alive
            }
            self.results.append(result)

            # Вивести короткий результат
            print()  # Новий рядок після прогресу
            print(f"\n  {'='*60}")
            print(f"  [{sim_number}/{self.count}] SIMULATION COMPLETED")
            print(f"  {'='*60}")
            print(f"  Duration:    {sim.step_count} steps")
            print(f"  Winner:      Side {winner} ({reason})")
            print(f"  Final state: A={pot_a_final:.0f}% ({side_a_alive} alive) | B={pot_b_final:.0f}% ({side_b_alive} alive)")
            print(f"  {'='*60}\n")

        except Exception as e:
            print(f"  [ERROR] Simulation {sim_number} failed: {e}")
            self.results.append({
                'number': sim_number,
                'error': str(e)
            })

    def _print_summary(self):
        """Вивести короткий підсумок серії"""
        duration = self.end_time - self.start_time
        successful = [r for r in self.results if 'error' not in r]
        failed = len(self.results) - len(successful)

        print("\n" + "=" * 70)
        print("BATCH SUMMARY".center(70))
        print("=" * 70)

        print(f"\nCompleted:  {len(successful)}/{self.count} simulations")
        if failed > 0:
            print(f"Failed:     {failed}")
        print(f"Duration:   {duration:.1f}s ({duration/len(successful):.1f}s per sim)")

        if successful:
            # Статистика переможців
            wins_a = sum(1 for r in successful if r['winner'] == 'A')
            wins_b = sum(1 for r in successful if r['winner'] == 'B')

            print(f"\nWinner statistics:")
            print(f"  Side A: {wins_a} wins ({wins_a/len(successful)*100:.1f}%)")
            print(f"  Side B: {wins_b} wins ({wins_b/len(successful)*100:.1f}%)")

            # Середня тривалість
            avg_steps = sum(r['steps'] for r in successful) / len(successful)
            min_steps = min(r['steps'] for r in successful)
            max_steps = max(r['steps'] for r in successful)

            print(f"\nBattle duration:")
            print(f"  Average: {avg_steps:.0f} steps")
            print(f"  Range:   {min_steps}-{max_steps} steps")

            # Середній фінальний потенціал
            avg_pot_a = sum(r['potential_a'] for r in successful) / len(successful)
            avg_pot_b = sum(r['potential_b'] for r in successful) / len(successful)

            print(f"\nFinal potential (average):")
            print(f"  Side A: {avg_pot_a:.1f}%")
            print(f"  Side B: {avg_pot_b:.1f}%")

        print("\n" + "=" * 70)

    def _run_consolidation(self):
        """Автоматично запустити консолідацію"""
        print("\nRunning consolidated analysis...")

        try:
            analyzer = ConsolidatedAnalyzer(logs_dir='logs')

            count = analyzer.find_analysis_files()
            if count == 0:
                print("  No analysis files found!")
                return

            valid_count = analyzer.load_all_data()
            if valid_count == 0:
                print("  No valid simulation data found!")
                return

            stats = analyzer.calculate_statistics()
            if not stats:
                print("  Failed to calculate statistics!")
                return

            output_file = analyzer.generate_report(stats)
            print(f"\n  SUCCESS! Consolidated report: {output_file}")
            print("\n" + "="*70)
            print("ALL SIMULATIONS COMPLETED SUCCESSFULLY!".center(70))
            print("="*70)
            print(f"\nTotal simulations: {valid_count}")
            print(f"Consolidated report: {output_file}")
            print("\nYou can now review:")
            print(f"  - Individual logs in: logs/combat/")
            print(f"  - Consolidated analysis: {output_file}")
            print("="*70 + "\n")

        except Exception as e:
            print(f"  WARNING: Consolidation failed: {e}")
            print("\n" + "="*70)
            print("BATCH SIMULATIONS COMPLETED".center(70))
            print("="*70)
            print("\nNote: Consolidation had issues, but individual simulations completed.")
            print("Check logs/combat/ for individual results.")
            print("="*70 + "\n")


def main():
    """Головна функція"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run batch simulations with progress tracking'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of simulations to run (default: 10)'
    )
    parser.add_argument(
        '--types',
        default='data/unit_types.xlsx',
        help='Path to unit types Excel file (default: data/unit_types.xlsx)'
    )
    parser.add_argument(
        '--instances',
        default='data/unit_instances.xlsx',
        help='Path to unit instances Excel file (default: data/unit_instances.xlsx)'
    )
    parser.add_argument(
        '--rules',
        default='data/engagement_rules.xlsx',
        help='Path to engagement rules Excel file (default: data/engagement_rules.xlsx)'
    )

    args = parser.parse_args()

    # Запустити серію
    batch = SimulationBatch(
        count=args.count,
        types_file=args.types,
        instances_file=args.instances,
        rules_file=args.rules
    )
    batch.run()

    return 0


if __name__ == '__main__':
    sys.exit(main())
