"""
Create test scenario with units closer together for RL training
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import os

def create_close_combat_scenario():
    """Create a scenario where units are close enough to engage"""

    # Create objects with units close together
    objects_data = []

    # Side A - at position (36.5, 47.5)
    base_x_a = 36.5
    base_y_a = 47.5

    # Side A: 3 tanks
    objects_data.append({
        'ID': 1,
        'Name': 'A_Tank_1',
        'Side': 'A',
        'Type': 'tank',
        'X_Coord': base_x_a,
        'Y_Coord': base_y_a,
        'Speed': 0.001,
        'Direction': 90,
        'HP': 100,
        'Max_HP': 100,
        'Range': 2.5,  # 2.5 km range
        'Attack_Power': 50,
        'Accuracy': 0.7,
        'Armor': 30,
        'Personnel_Count': 3
    })

    objects_data.append({
        'ID': 2,
        'Name': 'A_BMP_1',
        'Side': 'A',
        'Type': 'bmp',
        'X_Coord': base_x_a + 0.005,
        'Y_Coord': base_y_a,
        'Speed': 0.0015,
        'Direction': 90,
        'HP': 80,
        'Max_HP': 80,
        'Range': 1.8,
        'Attack_Power': 30,
        'Accuracy': 0.65,
        'Armor': 20,
        'Personnel_Count': 6
    })

    objects_data.append({
        'ID': 3,
        'Name': 'A_Infantry_1',
        'Side': 'A',
        'Type': 'infantry',
        'X_Coord': base_x_a - 0.005,
        'Y_Coord': base_y_a,
        'Speed': 0.0005,
        'Direction': 90,
        'HP': 50,
        'Max_HP': 50,
        'Range': 0.4,
        'Attack_Power': 20,
        'Accuracy': 0.6,
        'Armor': 5,
        'Personnel_Count': 10
    })

    # Side B - at position (36.52, 47.5) - about 2km away
    base_x_b = 36.52  # ~2km east
    base_y_b = 47.5

    # Side B: 2 tanks, 1 BMP
    objects_data.append({
        'ID': 11,
        'Name': 'B_Tank_1',
        'Side': 'B',
        'Type': 'tank',
        'X_Coord': base_x_b,
        'Y_Coord': base_y_b,
        'Speed': 0.001,
        'Direction': 270,
        'HP': 100,
        'Max_HP': 100,
        'Range': 2.5,
        'Attack_Power': 50,
        'Accuracy': 0.7,
        'Armor': 30,
        'Personnel_Count': 3
    })

    objects_data.append({
        'ID': 12,
        'Name': 'B_Tank_2',
        'Side': 'B',
        'Type': 'tank',
        'X_Coord': base_x_b + 0.005,
        'Y_Coord': base_y_b + 0.005,
        'Speed': 0.001,
        'Direction': 270,
        'HP': 100,
        'Max_HP': 100,
        'Range': 2.5,
        'Attack_Power': 50,
        'Accuracy': 0.7,
        'Armor': 30,
        'Personnel_Count': 3
    })

    objects_data.append({
        'ID': 13,
        'Name': 'B_BMP_1',
        'Side': 'B',
        'Type': 'bmp',
        'X_Coord': base_x_b - 0.005,
        'Y_Coord': base_y_b - 0.005,
        'Speed': 0.0015,
        'Direction': 270,
        'HP': 80,
        'Max_HP': 80,
        'Range': 1.8,
        'Attack_Power': 30,
        'Accuracy': 0.65,
        'Armor': 20,
        'Personnel_Count': 6
    })

    # Create DataFrame
    df = pd.DataFrame(objects_data)

    # Save to Excel
    output_path = 'data/test_objects.xlsx'
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Objects', index=False)

    print(f"✓ Created test scenario: {output_path}")
    print(f"  Side A: 3 units at ({base_x_a}, {base_y_a})")
    print(f"  Side B: 3 units at ({base_x_b}, {base_y_b})")
    print(f"  Distance: ~2.2 km (within tank range)")
    print(f"\nUnits will engage immediately!")

    return output_path


def main():
    print("="*60)
    print("CREATING TEST SCENARIO FOR RL TRAINING")
    print("="*60)
    print()

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Create test scenario
    scenario_path = create_close_combat_scenario()

    print("\n" + "="*60)
    print("ГОТОВО!")
    print("="*60)
    print("\nТепер можна використовувати:")
    print(f"  python visualize_training.py")
    print(f"  (або вказати objects_file='data/test_objects.xlsx' в коді)")
    print()
    print("Швидкий тест:")
    print("  python quick_test_combat.py")
    print("="*60)


if __name__ == '__main__':
    main()
