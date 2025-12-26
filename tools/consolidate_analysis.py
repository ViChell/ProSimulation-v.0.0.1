"""
Consolidated Analysis Tool

Цей інструмент читає всі файли analysis_*.txt з папки logs/,
розраховує середні показники за всі симуляції та створює
консолідований звіт.

Usage:
    python tools/consolidate_analysis.py
    python tools/consolidate_analysis.py --output custom_report.txt
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics


class ConsolidatedAnalyzer:
    """Аналізатор для консолідації результатів множинних симуляцій"""

    def __init__(self, logs_dir='logs'):
        self.logs_dir = Path(logs_dir)
        self.analysis_files = []
        self.simulations_data = []

    def find_analysis_files(self):
        """Знайти всі файли analysis_*.txt"""
        pattern = 'analysis_*.txt'
        self.analysis_files = sorted(
            self.logs_dir.glob(pattern),
            key=lambda f: f.stat().st_mtime
        )

        print(f"Found {len(self.analysis_files)} analysis files")
        return len(self.analysis_files)

    def parse_analysis_file(self, file_path):
        """
        Парсити файл аналізу та витягти дані

        Повертає dict з ключовими метриками
        """
        data = {
            'file': file_path.name,
            'timestamp': None,
            'winner': None,
            'total_steps': 0,
            'duration': 0,
            'sides': {}
        }

        try:
            # Знайти відповідний JSON файл з детальними даними
            combat_dir = self.logs_dir / 'combat'
            if combat_dir.exists():
                # Шукаємо JSON файли які не є analysis або summary
                json_files = [f for f in combat_dir.glob('combat_*.json')
                              if 'analysis' not in f.name
                              and 'latest' not in f.name
                              and 'summary' not in f.name
                              and f.stat().st_size > 0]  # Виключити порожні файли

                if json_files:
                    # Беремо найближчий по часу до текстового файлу
                    closest_json = min(
                        json_files,
                        key=lambda f: abs(f.stat().st_mtime - file_path.stat().st_mtime)
                    )

                    # Завантажити analysis JSON
                    analysis_json = closest_json.parent / f"{closest_json.stem}_analysis.json"
                    if analysis_json.exists():
                        with open(analysis_json, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            data.update(self._extract_from_json(json_data))

                    # Додатково прочитати основний combat JSON для матриці "хто кого вразив"
                    data['engagement_matrix'] = self._parse_combat_events(closest_json)

        except Exception as e:
            print(f"Warning: Could not parse {file_path.name}: {e}")

        return data

    def _parse_combat_events(self, combat_json_path):
        """
        Парсити combat JSON для створення матриці взаємодій між типами юнітів

        Повертає dict: {attacker_type: {target_type: {'hits': X, 'destroyed': Y}}}
        """
        matrix = defaultdict(lambda: defaultdict(lambda: {'hits': 0, 'destroyed': 0}))

        try:
            with open(combat_json_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_type = event.get('event_type')

                        if event_type in ['hit', 'destroyed']:
                            attacker_type = event.get('attacker', {}).get('type', 'unknown')
                            target_type = event.get('target', {}).get('type', 'unknown')

                            if event_type == 'hit':
                                matrix[attacker_type][target_type]['hits'] += 1
                            elif event_type == 'destroyed':
                                matrix[attacker_type][target_type]['destroyed'] += 1

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"  Warning: Could not parse combat events from {combat_json_path.name}: {e}")

        # Конвертувати defaultdict в звичайний dict
        return {k: dict(v) for k, v in matrix.items()}

    def _extract_from_json(self, json_data):
        """Витягти ключові метрики з JSON"""
        extracted = {}

        # Загальні дані
        if 'total_events' in json_data:
            extracted['total_events'] = json_data['total_events']

        # Дані по типах подій
        if 'by_type' in json_data:
            extracted['shots'] = json_data['by_type'].get('shot', 0)
            extracted['hits'] = json_data['by_type'].get('hit', 0)
            extracted['destroyed'] = json_data['by_type'].get('destroyed', 0)

        # Дані по типах юнітів
        if 'by_unit_type' in json_data:
            extracted['unit_types'] = {}
            for unit_type, type_data in json_data['by_unit_type'].items():
                extracted['unit_types'][unit_type] = {
                    'shots': type_data.get('shots', 0),
                    'hits': type_data.get('hits', 0),
                    'destroyed': type_data.get('destroyed', 0)
                }

        # Дані по сторонах
        if 'by_side' in json_data:
            extracted['sides'] = {}
            for side, side_data in json_data['by_side'].items():
                extracted['sides'][side] = {
                    'shots': side_data.get('shots', 0),
                    'hits': side_data.get('hits', 0),
                    'kills': side_data.get('kills', 0),
                    'destroyed': side_data.get('destroyed', 0)
                }

        # Дані про потенціал (для нових симуляцій)
        # Примітка: потенціал зберігається в summary JSON, а не в analysis JSON
        # Тому ми спробуємо знайти відповідний summary файл
        if 'potential' in json_data:
            extracted['potential'] = json_data['potential']

        # Статистика
        if 'statistics' in json_data:
            stats = json_data['statistics']
            if 'distances' in stats:
                extracted['avg_distance'] = stats['distances'].get('average', 0)
                extracted['min_distance'] = stats['distances'].get('min', 0)
                extracted['max_distance'] = stats['distances'].get('max', 0)

            if 'hit_chances' in stats:
                extracted['avg_hit_chance'] = stats['hit_chances'].get('average', 0)

            if 'damages' in stats:
                extracted['avg_damage'] = stats['damages'].get('average', 0)
                extracted['min_damage'] = stats['damages'].get('min', 0)
                extracted['max_damage'] = stats['damages'].get('max', 0)

        # Визначити переможця
        # Нова логіка: переможець визначається по потенціалу (якщо є дані)
        # Стара логіка: по кількості знищених (для сумісності зі старими симуляціями)
        if 'sides' in extracted and extracted['sides']:
            # Спробувати визначити по потенціалу (нові симуляції)
            if 'potential' in extracted:
                potential_a = extracted['potential'].get('A', {})
                potential_b = extracted['potential'].get('B', {})

                # Якщо є дані про потенціал, використати їх
                if 'percent' in potential_a and 'percent' in potential_b:
                    # Side програла якщо потенціал <= 30%
                    if potential_a['percent'] <= 30:
                        extracted['winner'] = 'B'
                    elif potential_b['percent'] <= 30:
                        extracted['winner'] = 'A'
                    else:
                        # Якщо обидві вище 30%, визначити по кількості kills
                        side_a_kills = extracted['sides'].get('A', {}).get('kills', 0)
                        side_b_kills = extracted['sides'].get('B', {}).get('kills', 0)
                        extracted['winner'] = 'A' if side_a_kills > side_b_kills else 'B'
                else:
                    # Fallback до старої логіки
                    extracted['winner'] = self._determine_winner_old_logic(extracted)
            else:
                # Стара логіка для сумісності
                extracted['winner'] = self._determine_winner_old_logic(extracted)

        return extracted

    def _determine_winner_old_logic(self, extracted):
        """Old logic for determining winner (for backwards compatibility)"""
        side_a_kills = extracted['sides'].get('A', {}).get('kills', 0)
        side_b_kills = extracted['sides'].get('B', {}).get('kills', 0)

        # Side A виграла якщо знищила всіх ворогів Side B (90 юнітів)
        # Side B виграла якщо знищила всіх ворогів Side A (200 юнітів)
        if side_a_kills >= 90:  # Side A знищила всіх з Side B
            return 'A'
        elif side_b_kills >= 200:  # Side B знищила всіх з Side A
            return 'B'
        else:
            # Якщо обидві живі, визначити по поточному балансу
            return 'A' if side_a_kills > side_b_kills else 'B'

    def load_all_data(self):
        """Завантажити дані з усіх файлів аналізу"""
        print("\nLoading simulation data...")

        for file_path in self.analysis_files:
            print(f"  Processing {file_path.name}...")
            data = self.parse_analysis_file(file_path)
            if data.get('total_events', 0) > 0:  # Тільки файли з даними
                self.simulations_data.append(data)

        print(f"\nLoaded {len(self.simulations_data)} valid simulations")
        return len(self.simulations_data)

    def calculate_statistics(self):
        """Розрахувати консолідовану статистику"""
        if not self.simulations_data:
            return None

        stats = {
            'total_simulations': len(self.simulations_data),
            'winners': defaultdict(int),
            'averages': {},
            'ranges': {},
            'side_stats': defaultdict(lambda: defaultdict(list)),
            'unit_type_stats': defaultdict(lambda: defaultdict(list)),
            'engagement_matrix': defaultdict(lambda: defaultdict(lambda: {'hits': [], 'destroyed': []}))
        }

        # Збір даних
        for sim in self.simulations_data:
            # Підрахунок переможців
            if sim.get('winner'):
                stats['winners'][sim['winner']] += 1

            # Збір метрик для усереднення
            for key in ['shots', 'hits', 'destroyed', 'total_events',
                        'avg_distance', 'avg_hit_chance', 'avg_damage']:
                if key in sim:
                    if key not in stats['averages']:
                        stats['averages'][key] = []
                    stats['averages'][key].append(sim[key])

            # Збір даних по сторонах
            if 'sides' in sim:
                for side, side_data in sim['sides'].items():
                    for metric, value in side_data.items():
                        stats['side_stats'][side][metric].append(value)

            # Збір даних по типах юнітів
            if 'unit_types' in sim:
                for unit_type, type_data in sim['unit_types'].items():
                    for metric, value in type_data.items():
                        stats['unit_type_stats'][unit_type][metric].append(value)

            # Збір матриці взаємодій
            if 'engagement_matrix' in sim:
                for attacker_type, targets in sim['engagement_matrix'].items():
                    for target_type, data in targets.items():
                        stats['engagement_matrix'][attacker_type][target_type]['hits'].append(data['hits'])
                        stats['engagement_matrix'][attacker_type][target_type]['destroyed'].append(data['destroyed'])

        # Розрахунок середніх та діапазонів
        calculated_averages = {}
        calculated_ranges = {}

        for key, values in stats['averages'].items():
            if values:
                calculated_averages[key] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values)
                }

        # Розрахунок по сторонах
        calculated_sides = {}
        for side, metrics in stats['side_stats'].items():
            calculated_sides[side] = {}
            for metric, values in metrics.items():
                if values:
                    calculated_sides[side][metric] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values)
                    }

        # Розрахунок по типах юнітів
        calculated_unit_types = {}
        for unit_type, metrics in stats['unit_type_stats'].items():
            calculated_unit_types[unit_type] = {}
            for metric, values in metrics.items():
                if values:
                    calculated_unit_types[unit_type][metric] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values)
                    }

        # Розрахунок матриці взаємодій
        calculated_engagement_matrix = {}
        for attacker_type, targets in stats['engagement_matrix'].items():
            calculated_engagement_matrix[attacker_type] = {}
            for target_type, data in targets.items():
                hits_values = data['hits']
                destroyed_values = data['destroyed']

                calculated_engagement_matrix[attacker_type][target_type] = {
                    'hits': {
                        'mean': statistics.mean(hits_values) if hits_values else 0,
                        'total': sum(hits_values)
                    },
                    'destroyed': {
                        'mean': statistics.mean(destroyed_values) if destroyed_values else 0,
                        'total': sum(destroyed_values)
                    }
                }

        stats['calculated_averages'] = calculated_averages
        stats['calculated_sides'] = calculated_sides
        stats['calculated_unit_types'] = calculated_unit_types
        stats['calculated_engagement_matrix'] = calculated_engagement_matrix

        return stats

    def generate_report(self, stats, output_file=None):
        """Створити консолідований звіт"""
        if output_file is None:
            timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
            output_file = self.logs_dir / f'consolidated_analysis_{timestamp}.txt'
        else:
            output_file = Path(output_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            # Заголовок
            f.write("=" * 80 + "\n")
            f.write("CONSOLIDATED ANALYSIS REPORT\n".center(80))
            f.write("=" * 80 + "\n\n")

            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total simulations analyzed: {stats['total_simulations']}\n")
            f.write(f"Analysis files processed: {len(self.analysis_files)}\n")
            f.write("\n")

            # Статистика переможців
            f.write("=" * 80 + "\n")
            f.write("WINNER STATISTICS\n")
            f.write("=" * 80 + "\n\n")

            total_sims = stats['total_simulations']
            for winner, count in sorted(stats['winners'].items()):
                percentage = (count / total_sims * 100) if total_sims > 0 else 0
                f.write(f"Side {winner}: {count} wins ({percentage:.1f}%)\n")

            if stats['winners']:
                dominant = max(stats['winners'].items(), key=lambda x: x[1])
                f.write(f"\nDominant side: {dominant[0]} with {dominant[1]} victories\n")

            # Загальна статистика
            f.write("\n" + "=" * 80 + "\n")
            f.write("OVERALL STATISTICS (across all simulations)\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"{'Metric':<25} {'Mean':<12} {'Median':<12} {'StdDev':<12} {'Min':<10} {'Max':<10}\n")
            f.write("-" * 80 + "\n")

            # Виведення метрик
            metric_labels = {
                'total_events': 'Total Events',
                'shots': 'Total Shots',
                'hits': 'Total Hits',
                'destroyed': 'Total Destroyed',
                'avg_distance': 'Avg Distance (km)',
                'avg_hit_chance': 'Avg Hit Chance',
                'avg_damage': 'Avg Damage'
            }

            for key, label in metric_labels.items():
                if key in stats['calculated_averages']:
                    data = stats['calculated_averages'][key]
                    f.write(f"{label:<25} "
                           f"{data['mean']:<12.2f} "
                           f"{data['median']:<12.2f} "
                           f"{data['stdev']:<12.2f} "
                           f"{data['min']:<10.2f} "
                           f"{data['max']:<10.2f}\n")

            # Accuracy
            if 'shots' in stats['calculated_averages'] and 'hits' in stats['calculated_averages']:
                shots_mean = stats['calculated_averages']['shots']['mean']
                hits_mean = stats['calculated_averages']['hits']['mean']
                accuracy = (hits_mean / shots_mean * 100) if shots_mean > 0 else 0
                f.write(f"\nOverall Accuracy: {accuracy:.2f}%\n")

            # Статистика по сторонах
            f.write("\n" + "=" * 80 + "\n")
            f.write("STATISTICS BY SIDE\n")
            f.write("=" * 80 + "\n\n")

            for side in sorted(stats['calculated_sides'].keys()):
                f.write(f"\nSide {side}:\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'Metric':<20} {'Mean':<12} {'Median':<12} {'StdDev':<12}\n")
                f.write("-" * 40 + "\n")

                side_data = stats['calculated_sides'][side]
                for metric in ['shots', 'hits', 'kills', 'destroyed']:
                    if metric in side_data:
                        data = side_data[metric]
                        f.write(f"{metric.capitalize():<20} "
                               f"{data['mean']:<12.2f} "
                               f"{data['median']:<12.2f} "
                               f"{data['stdev']:<12.2f}\n")

                # Accuracy для сторони
                if 'shots' in side_data and 'hits' in side_data:
                    shots_mean = side_data['shots']['mean']
                    hits_mean = side_data['hits']['mean']
                    accuracy = (hits_mean / shots_mean * 100) if shots_mean > 0 else 0
                    f.write(f"\nAccuracy: {accuracy:.2f}%\n")

            # Статистика по типах юнітів
            if stats.get('calculated_unit_types'):
                f.write("\n" + "=" * 80 + "\n")
                f.write("STATISTICS BY UNIT TYPE\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"{'Unit Type':<15} {'Shots':<12} {'Hits':<12} {'Destroyed':<12} {'Accuracy':<10}\n")
                f.write("-" * 80 + "\n")

                for unit_type in sorted(stats['calculated_unit_types'].keys()):
                    type_data = stats['calculated_unit_types'][unit_type]

                    shots = type_data.get('shots', {}).get('mean', 0)
                    hits = type_data.get('hits', {}).get('mean', 0)
                    destroyed = type_data.get('destroyed', {}).get('mean', 0)
                    accuracy = (hits / shots * 100) if shots > 0 else 0

                    f.write(f"{unit_type.capitalize():<15} "
                           f"{shots:<12.2f} "
                           f"{hits:<12.2f} "
                           f"{destroyed:<12.2f} "
                           f"{accuracy:<10.2f}%\n")

            # Матриця взаємодій (хто кого вразив/знищив)
            if stats.get('calculated_engagement_matrix'):
                f.write("\n" + "=" * 80 + "\n")
                f.write("ENGAGEMENT MATRIX (Attacker vs Target)\n")
                f.write("=" * 80 + "\n\n")

                f.write("Shows average hits and kills across all simulations\n\n")

                for attacker_type in sorted(stats['calculated_engagement_matrix'].keys()):
                    f.write(f"\n{attacker_type.upper()} attacking:\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"{'Target Type':<15} {'Avg Hits':<15} {'Total Hits':<15} {'Avg Kills':<15} {'Total Kills':<15}\n")
                    f.write("-" * 60 + "\n")

                    targets = stats['calculated_engagement_matrix'][attacker_type]
                    for target_type in sorted(targets.keys()):
                        data = targets[target_type]

                        avg_hits = data['hits']['mean']
                        total_hits = data['hits']['total']
                        avg_destroyed = data['destroyed']['mean']
                        total_destroyed = data['destroyed']['total']

                        f.write(f"{target_type.capitalize():<15} "
                               f"{avg_hits:<15.2f} "
                               f"{total_hits:<15.0f} "
                               f"{avg_destroyed:<15.2f} "
                               f"{total_destroyed:<15.0f}\n")

            # Список файлів
            f.write("\n" + "=" * 80 + "\n")
            f.write("ANALYZED FILES\n")
            f.write("=" * 80 + "\n\n")

            for i, file_path in enumerate(self.analysis_files, 1):
                f.write(f"{i:3d}. {file_path.name}\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")

        print(f"\nConsolidated report saved to: {output_file}")
        return output_file


def main():
    """Головна функція"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Consolidate multiple simulation analysis files'
    )
    parser.add_argument(
        '--logs-dir',
        default='logs',
        help='Directory containing analysis files (default: logs)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: logs/consolidated_analysis_DD_MM_YYYY_HH_MM_SS.txt)'
    )

    args = parser.parse_args()

    # Створити аналізатор
    analyzer = ConsolidatedAnalyzer(logs_dir=args.logs_dir)

    # Знайти файли
    count = analyzer.find_analysis_files()
    if count == 0:
        print("No analysis files found!")
        return 1

    # Завантажити дані
    valid_count = analyzer.load_all_data()
    if valid_count == 0:
        print("No valid simulation data found!")
        return 1

    # Розрахувати статистику
    print("\nCalculating consolidated statistics...")
    stats = analyzer.calculate_statistics()

    if not stats:
        print("Failed to calculate statistics!")
        return 1

    # Створити звіт
    print("\nGenerating report...")
    output_file = analyzer.generate_report(stats, output_file=args.output)

    print(f"\n✓ Success! Analyzed {stats['total_simulations']} simulations")
    print(f"✓ Report saved to: {output_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())