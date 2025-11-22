"""
Утиліта для аналізу логів бойової симуляції
Аналізує JSON логи бойових подій та генерує статистику
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class CombatLogAnalyzer:
    """Аналізатор логів бойових подій"""

    def __init__(self, log_file):
        self.log_file = Path(log_file)
        self.events = []
        self.stats = {}

    def load_events(self):
        """Завантажити події з JSON файлу"""
        print(f"Loading events from {self.log_file}")

        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event = json.loads(line.strip())
                    self.events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_num}: {e}")

        print(f"Loaded {len(self.events)} events\n")

    def analyze(self):
        """Провести повний аналіз"""
        if not self.events:
            print("No events to analyze")
            return

        self.stats = {
            'total_events': len(self.events),
            'by_type': defaultdict(int),
            'by_step': defaultdict(lambda: {'total': 0, 'types': defaultdict(int)}),
            'by_attacker': defaultdict(lambda: {'shots': 0, 'hits': 0, 'destroyed': 0, 'name': '', 'type': '', 'side': ''}),
            'by_unit_type': defaultdict(lambda: {'shots': 0, 'hits': 0, 'destroyed': 0}),
            'by_side': defaultdict(lambda: {'shots': 0, 'hits': 0, 'destroyed': 0, 'kills': 0}),
            'distances': [],
            'hit_chances': [],
            'damages': []
        }

        for event in self.events:
            event_type = event['event_type']
            step = event['step']
            attacker = event['attacker']
            target = event['target']

            # За типом події
            self.stats['by_type'][event_type] += 1

            # За кроками
            self.stats['by_step'][step]['total'] += 1
            self.stats['by_step'][step]['types'][event_type] += 1

            # За атакуючими
            attacker_id = attacker['id']
            self.stats['by_attacker'][attacker_id]['name'] = attacker['name']
            self.stats['by_attacker'][attacker_id]['type'] = attacker['type']
            self.stats['by_attacker'][attacker_id]['side'] = attacker['side']

            # За типом юнітів
            attacker_type = attacker['type']
            attacker_side = attacker['side']

            if event_type == 'shot':
                self.stats['by_attacker'][attacker_id]['shots'] += 1
                self.stats['by_unit_type'][attacker_type]['shots'] += 1
                self.stats['by_side'][attacker_side]['shots'] += 1

                if 'distance' in event:
                    self.stats['distances'].append(event['distance'])
                if 'hit_chance' in event:
                    self.stats['hit_chances'].append(event['hit_chance'])

            elif event_type == 'hit':
                self.stats['by_attacker'][attacker_id]['hits'] += 1
                self.stats['by_unit_type'][attacker_type]['hits'] += 1
                self.stats['by_side'][attacker_side]['hits'] += 1

                if 'damage' in event:
                    self.stats['damages'].append(event['damage'])

            elif event_type == 'destroyed':
                self.stats['by_attacker'][attacker_id]['destroyed'] += 1
                self.stats['by_unit_type'][attacker_type]['destroyed'] += 1
                self.stats['by_side'][attacker_side]['kills'] += 1

    def print_summary(self, output_file=None):
        """Вивести загальну статистику

        Args:
            output_file: Опціональний файл для запису результатів
        """
        # Визначити куди виводити
        import sys
        original_stdout = sys.stdout
        f = None

        try:
            if output_file:
                f = open(output_file, 'w', encoding='utf-8')
                sys.stdout = f

            print("="*70)
            print(" "*25 + "COMBAT LOG ANALYSIS")
            print("="*70)
            print()

            # Загальна статистика
            print("📊 GENERAL STATISTICS")
            print("-"*70)
            print(f"Total events:        {self.stats['total_events']}")
            print(f"Total steps:         {len(self.stats['by_step'])}")
            print()

            # За типом події
            print("Events by type:")
            for event_type, count in sorted(self.stats['by_type'].items()):
                print(f"  {event_type:15s}: {count:6d}")
            print()

            # Статистика по сторонам
            print("🎯 STATISTICS BY SIDE")
            print("-"*70)
            for side in sorted(self.stats['by_side'].keys()):
                data = self.stats['by_side'][side]
                accuracy = (data['hits'] / data['shots'] * 100) if data['shots'] > 0 else 0
                print(f"\nSide {side}:")
                print(f"  Shots fired:     {data['shots']}")
                print(f"  Hits landed:     {data['hits']}")
                print(f"  Accuracy:        {accuracy:.1f}%")
                print(f"  Enemy destroyed: {data['kills']}")
            print()

            # Статистика по типам юнітів
            print("🔫 STATISTICS BY UNIT TYPE")
            print("-"*70)
            print(f"{'Type':<15} {'Shots':>8} {'Hits':>8} {'Kills':>8} {'Accuracy':>10}")
            print("-"*70)

            for unit_type in sorted(self.stats['by_unit_type'].keys()):
                data = self.stats['by_unit_type'][unit_type]
                accuracy = (data['hits'] / data['shots'] * 100) if data['shots'] > 0 else 0
                print(f"{unit_type:<15} {data['shots']:>8} {data['hits']:>8} {data['destroyed']:>8} {accuracy:>9.1f}%")
            print()

            # Топ стрільців
            print("🏆 TOP PERFORMERS")
            print("-"*70)
            top_killers = sorted(
                [(k, v) for k, v in self.stats['by_attacker'].items() if v['destroyed'] > 0],
                key=lambda x: x[1]['destroyed'],
                reverse=True
            )[:10]

            if top_killers:
                print(f"{'Rank':<6} {'Name':<20} {'Type':<10} {'Side':<6} {'Kills':>7} {'Acc%':>7}")
                print("-"*70)
                for rank, (unit_id, data) in enumerate(top_killers, 1):
                    accuracy = (data['hits'] / data['shots'] * 100) if data['shots'] > 0 else 0
                    print(f"{rank:<6} {data['name']:<20} {data['type']:<10} {data['side']:<6} {data['destroyed']:>7} {accuracy:>6.1f}%")
            else:
                print("No kills recorded")
            print()

            # Статистика дистанцій
            if self.stats['distances']:
                avg_distance = sum(self.stats['distances']) / len(self.stats['distances'])
                min_distance = min(self.stats['distances'])
                max_distance = max(self.stats['distances'])

                print("📏 DISTANCE STATISTICS")
                print("-"*70)
                print(f"Average engagement distance: {avg_distance:.2f} km")
                print(f"Minimum distance:            {min_distance:.2f} km")
                print(f"Maximum distance:            {max_distance:.2f} km")
                print()

            # Статистика шансів влучення
            if self.stats['hit_chances']:
                avg_hit_chance = sum(self.stats['hit_chances']) / len(self.stats['hit_chances'])

                print("🎲 HIT CHANCE STATISTICS")
                print("-"*70)
                print(f"Average hit chance: {avg_hit_chance:.1%}")
                print()

            # Статистика пошкоджень
            if self.stats['damages']:
                avg_damage = sum(self.stats['damages']) / len(self.stats['damages'])
                min_damage = min(self.stats['damages'])
                max_damage = max(self.stats['damages'])

                print("💥 DAMAGE STATISTICS")
                print("-"*70)
                print(f"Average damage: {avg_damage:.1f}")
                print(f"Minimum damage: {min_damage:.1f}")
                print(f"Maximum damage: {max_damage:.1f}")
                print()

            print("="*70)

        finally:
            # Відновити stdout
            sys.stdout = original_stdout
            if f:
                f.close()

    def export_to_json(self, output_file):
        """Експортувати статистику в JSON"""
        # Конвертувати defaultdict у звичайні dict
        export_stats = {
            'total_events': self.stats['total_events'],
            'by_type': dict(self.stats['by_type']),
            'by_step': {k: dict(v) for k, v in self.stats['by_step'].items()},
            'by_attacker': {k: dict(v) for k, v in self.stats['by_attacker'].items()},
            'by_unit_type': {k: dict(v) for k, v in self.stats['by_unit_type'].items()},
            'by_side': {k: dict(v) for k, v in self.stats['by_side'].items()},
            'statistics': {}
        }

        # Додати агреговану статистику
        if self.stats['distances']:
            export_stats['statistics']['distances'] = {
                'average': sum(self.stats['distances']) / len(self.stats['distances']),
                'min': min(self.stats['distances']),
                'max': max(self.stats['distances'])
            }

        if self.stats['hit_chances']:
            export_stats['statistics']['hit_chances'] = {
                'average': sum(self.stats['hit_chances']) / len(self.stats['hit_chances'])
            }

        if self.stats['damages']:
            export_stats['statistics']['damages'] = {
                'average': sum(self.stats['damages']) / len(self.stats['damages']),
                'min': min(self.stats['damages']),
                'max': max(self.stats['damages'])
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_stats, f, indent=2, ensure_ascii=False)

        print(f"Statistics exported to {output_file}")


def analyze_latest_log(output_txt=None):
    """
    Проаналізувати останній лог автоматично

    Args:
        output_txt: Шлях до файлу для запису результатів (якщо None, виводить в консоль)

    Returns:
        True якщо успішно, False якщо помилка
    """
    # Спробувати знайти останній лог
    log_dir = Path('logs/combat')
    if not log_dir.exists():
        print(f"Error: Combat log directory not found: {log_dir}")
        return False

    json_files = list(log_dir.glob('combat_*.json'))
    json_files = [f for f in json_files if 'summary' not in f.name and 'latest' not in f.name]

    if not json_files:
        print("Error: No combat log files found")
        return False

    # Знайти найновіший файл
    log_file = max(json_files, key=lambda f: f.stat().st_mtime)

    try:
        # Створити аналізатор
        analyzer = CombatLogAnalyzer(log_file)

        # Завантажити та проаналізувати
        analyzer.load_events()
        analyzer.analyze()

        # Вивести результати
        analyzer.print_summary(output_file=output_txt)

        # Експортувати статистику в JSON
        json_output = log_file.with_name(log_file.stem + '_analysis.json')
        analyzer.export_to_json(json_output)

        return True

    except Exception as e:
        print(f"Error analyzing log: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Головна функція"""
    if len(sys.argv) < 2:
        # Спробувати знайти останній лог
        log_dir = Path('logs/combat')
        if log_dir.exists():
            json_files = list(log_dir.glob('combat_*.json'))
            json_files = [f for f in json_files if 'summary' not in f.name and 'latest' not in f.name]
            if json_files:
                # Сортувати за часом модифікації
                log_file = max(json_files, key=lambda f: f.stat().st_mtime)
                print(f"Using most recent log file: {log_file}\n")
            else:
                print("Usage: python log_analyzer.py <path_to_combat_log.json>")
                print("\nOr place this script in the project root with logs/combat/ directory")
                sys.exit(1)
        else:
            print("Usage: python log_analyzer.py <path_to_combat_log.json>")
            sys.exit(1)
    else:
        log_file = Path(sys.argv[1])

    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)

    # Створити аналізатор
    analyzer = CombatLogAnalyzer(log_file)

    # Завантажити та проаналізувати
    analyzer.load_events()
    analyzer.analyze()

    # Вивести результати
    analyzer.print_summary()

    # Експортувати статистику
    output_file = log_file.with_name(log_file.stem + '_analysis.json')
    analyzer.export_to_json(output_file)


if __name__ == '__main__':
    main()
