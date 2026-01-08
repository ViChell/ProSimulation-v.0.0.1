"""
Data Migration Tool: objects.xlsx -> Normalized Structure

Migrates denormalized objects.xlsx to normalized structure:
- unit_types.xlsx: Reference table of unit characteristics
- unit_instances.xlsx: Individual unit instances with coordinates
- engagement_rules.xlsx: Renamed from sets.xlsx

Usage:
    python tools/migrate_data.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil


class DataMigrator:
    """Migrates combat simulation data to normalized structure"""

    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / 'backup'

    def backup_old_files(self):
        """Create backup of original files"""
        print("\n" + "="*70)
        print("STEP 1: BACKING UP ORIGINAL FILES")
        print("="*70)

        # Create backup directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'backup_{timestamp}'
        backup_path.mkdir(parents=True, exist_ok=True)

        # Backup objects.xlsx
        objects_file = self.data_dir / 'objects.xlsx'
        if objects_file.exists():
            backup_file = backup_path / 'objects.xlsx'
            shutil.copy2(objects_file, backup_file)
            print(f"+ Backed up: {objects_file} -> {backup_file}")
        else:
            print(f"x Warning: {objects_file} not found!")
            return False

        # Backup sets.xlsx
        sets_file = self.data_dir / 'sets.xlsx'
        if sets_file.exists():
            backup_file = backup_path / 'sets.xlsx'
            shutil.copy2(sets_file, backup_file)
            print(f"+ Backed up: {sets_file} -> {backup_file}")

        print(f"\nBackup location: {backup_path}")
        return True

    def extract_unit_types(self, objects_df):
        """Extract unique unit types from objects.xlsx"""
        print("\n" + "="*70)
        print("STEP 2: EXTRACTING UNIQUE UNIT TYPES")
        print("="*70)

        # Define characteristic columns
        char_columns = ['Type', 'Max_HP', 'Range', 'Attack_Power',
                       'Accuracy', 'Armor', 'Speed', 'Personnel_Count']

        # Group by characteristics to find unique types
        unique_types = objects_df.groupby(char_columns).size().reset_index(name='instances_count')

        print(f"\nFound {len(unique_types)} unique unit type combinations:")
        print(f"  - {len(unique_types[unique_types['Type'] == 'tank'])} tank variants")
        print(f"  - {len(unique_types[unique_types['Type'] == 'bmp'])} bmp variants")
        print(f"  - {len(unique_types[unique_types['Type'] == 'infantry'])} infantry variants")

        # Create type_id based on characteristics
        type_ids = []
        type_names = []

        # Counters for each class
        counters = {'tank': 1, 'bmp': 1, 'infantry': 1, 'mortar': 1, 'artillery': 1, 'uav': 1}

        for _, row in unique_types.iterrows():
            unit_class = row['Type']

            # Generate descriptive type_id
            if unit_class == 'tank':
                hp = int(row['Max_HP'])
                range_val = row['Range']
                if hp == 100 and range_val == 2.5:
                    type_id = 'T72B3'
                    type_name = 'T-72B3'
                elif hp == 110 and range_val == 2.8:
                    type_id = 'T80BVM'
                    type_name = 'T-80BVM'
                elif hp == 120 and range_val == 2.8:
                    type_id = 'T90M'
                    type_name = 'T-90M'
                else:
                    type_id = f'TANK_{counters["tank"]}'
                    type_name = f'Tank Type {counters["tank"]}'
                    counters['tank'] += 1

            elif unit_class == 'bmp':
                hp = int(row['Max_HP'])
                range_val = row['Range']
                if hp == 60 and range_val == 1.5:
                    type_id = 'BMP2'
                    type_name = 'BMP-2'
                elif hp == 50 and range_val == 1.2:
                    type_id = 'BTR80'
                    type_name = 'BTR-80'
                elif hp == 55 and range_val == 1.5:
                    type_id = 'BMP1'
                    type_name = 'BMP-1'
                elif hp == 65 and range_val == 1.8:
                    type_id = 'BMP3'
                    type_name = 'BMP-3'
                else:
                    type_id = f'BMP_{counters["bmp"]}'
                    type_name = f'BMP Type {counters["bmp"]}'
                    counters['bmp'] += 1

            elif unit_class == 'infantry':
                type_id = 'INF_RIFLE'
                type_name = 'Rifleman'

            else:
                type_id = f'{unit_class.upper()}_{counters[unit_class]}'
                type_name = f'{unit_class.title()} Type {counters[unit_class]}'
                counters[unit_class] += 1

            type_ids.append(type_id)
            type_names.append(type_name)

        # Build unit_types DataFrame
        unit_types = pd.DataFrame({
            'type_id': type_ids,
            'type_name': type_names,
            'class': unique_types['Type'].values,
            'max_hp': unique_types['Max_HP'].values,
            'armor': unique_types['Armor'].values,
            'range': unique_types['Range'].values,
            'attack_power': unique_types['Attack_Power'].values,
            'accuracy': unique_types['Accuracy'].values,
            'speed': unique_types['Speed'].values,
            'personnel_count': unique_types['Personnel_Count'].values
        })

        # Display created types
        print("\nCreated unit types:")
        for _, row in unit_types.iterrows():
            print(f"  {row['type_id']:12} - {row['type_name']:15} "
                  f"(HP={row['max_hp']:3.0f}, Range={row['range']:.1f}km, "
                  f"Attack={row['attack_power']:2.0f})")

        return unit_types

    def create_instances(self, objects_df, unit_types_df):
        """Create unit instances from objects.xlsx"""
        print("\n" + "="*70)
        print("STEP 3: CREATING UNIT INSTANCES")
        print("="*70)

        # Create lookup dictionary for type_id
        type_lookup = {}
        for _, type_row in unit_types_df.iterrows():
            key = (
                type_row['class'],
                float(type_row['max_hp']),
                float(type_row['range']),
                float(type_row['attack_power']),
                float(type_row['accuracy']),
                float(type_row['armor']),
                float(type_row['speed']),
                int(type_row['personnel_count'])
            )
            type_lookup[key] = type_row['type_id']

        # Map each unit to its type_id
        type_ids = []
        for _, row in objects_df.iterrows():
            key = (
                row['Type'],
                float(row['Max_HP']),
                float(row['Range']),
                float(row['Attack_Power']),
                float(row['Accuracy']),
                float(row['Armor']),
                float(row['Speed']),
                int(row['Personnel_Count'])
            )
            type_id = type_lookup.get(key, 'UNKNOWN')
            type_ids.append(type_id)

        # Create instances DataFrame
        instances = pd.DataFrame({
            'id': objects_df['ID'].astype(int),
            'type_id': type_ids,
            'side': objects_df['Side'],
            'x_coord': objects_df['X_Coord'].astype(float),
            'y_coord': objects_df['Y_Coord'].astype(float),
            'direction': objects_df['Direction'].astype(int)
        })

        # Statistics
        print(f"\nCreated {len(instances)} unit instances:")
        print(f"  Side A: {len(instances[instances['side'] == 'A'])} units")
        print(f"  Side B: {len(instances[instances['side'] == 'B'])} units")

        # Distribution by type
        print("\nDistribution by type:")
        type_counts = instances['type_id'].value_counts()
        for type_id, count in type_counts.items():
            type_name = unit_types_df[unit_types_df['type_id'] == type_id]['type_name'].iloc[0]
            print(f"  {type_id:12} ({type_name:15}): {count:3} instances")

        return instances

    def save_normalized_files(self, unit_types_df, instances_df):
        """Save normalized Excel files"""
        print("\n" + "="*70)
        print("STEP 4: SAVING NORMALIZED FILES")
        print("="*70)

        # Save unit_types.xlsx
        types_file = self.data_dir / 'unit_types.xlsx'
        unit_types_df.to_excel(types_file, sheet_name='UnitTypes', index=False)
        print(f"+ Created: {types_file}")
        print(f"  - {len(unit_types_df)} unit types")

        # Save unit_instances.xlsx
        instances_file = self.data_dir / 'unit_instances.xlsx'
        instances_df.to_excel(instances_file, sheet_name='Units', index=False)
        print(f"+ Created: {instances_file}")
        print(f"  - {len(instances_df)} unit instances")

        # Rename sets.xlsx to engagement_rules.xlsx
        old_rules = self.data_dir / 'sets.xlsx'
        new_rules = self.data_dir / 'engagement_rules.xlsx'
        if old_rules.exists() and not new_rules.exists():
            shutil.copy2(old_rules, new_rules)
            print(f"+ Created: {new_rules} (copy of sets.xlsx)")

    def migrate(self):
        """Run complete migration"""
        print("\n" + "="*70)
        print("DATA MIGRATION: objects.xlsx -> Normalized Structure")
        print("="*70)
        print(f"Data directory: {self.data_dir.absolute()}")

        # Step 1: Backup
        if not self.backup_old_files():
            print("\nx Migration aborted: Could not backup files")
            return False

        # Load objects.xlsx
        objects_file = self.data_dir / 'objects.xlsx'
        try:
            objects_df = pd.read_excel(objects_file, sheet_name='Objects')
            print(f"\n+ Loaded {len(objects_df)} units from {objects_file}")
        except Exception as e:
            print(f"\nx Error loading {objects_file}: {e}")
            return False

        # Step 2: Extract types
        try:
            unit_types_df = self.extract_unit_types(objects_df)
        except Exception as e:
            print(f"\nx Error extracting unit types: {e}")
            return False

        # Step 3: Create instances
        try:
            instances_df = self.create_instances(objects_df, unit_types_df)
        except Exception as e:
            print(f"\nx Error creating instances: {e}")
            return False

        # Step 4: Save files
        try:
            self.save_normalized_files(unit_types_df, instances_df)
        except Exception as e:
            print(f"\nx Error saving files: {e}")
            return False

        # Success!
        print("\n" + "="*70)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nNew file structure:")
        print(f"  + {self.data_dir / 'unit_types.xlsx'}")
        print(f"  + {self.data_dir / 'unit_instances.xlsx'}")
        print(f"  + {self.data_dir / 'engagement_rules.xlsx'}")
        print(f"\nOriginal files backed up to: {self.backup_dir}")
        print("\nNext steps:")
        print("  1. Review the new files to verify correctness")
        print("  2. Run migration of code: modify DataLoader")
        print("="*70 + "\n")

        return True


def main():
    """Main entry point"""
    migrator = DataMigrator(data_dir='data')
    success = migrator.migrate()
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
