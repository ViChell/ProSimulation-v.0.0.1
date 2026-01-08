import pandas as pd
from .logging_config import SimulationLogger


class DataLoader:
    """Loads military unit data from normalized Excel files"""

    def __init__(self, types_file='data/unit_types.xlsx', instances_file='data/unit_instances.xlsx'):
        self.types_file = types_file
        self.instances_file = instances_file
        self.unit_types = {}  # {type_id: {...characteristics}}
        self.units_data = []
        self.logger = SimulationLogger.get_logger('data_loader')

    def load_unit_types(self):
        """Load unit types reference table"""
        try:
            self.logger.info(f"Loading unit types from {self.types_file}")
            df = pd.read_excel(self.types_file, sheet_name='UnitTypes')

            self.unit_types = {}
            for _, row in df.iterrows():
                type_id = row['type_id']
                self.unit_types[type_id] = {
                    'type_name': row['type_name'],
                    'class': row['class'],
                    'max_hp': float(row['max_hp']),
                    'armor': float(row['armor']),
                    'range': float(row['range']),
                    'attack_power': float(row['attack_power']),
                    'accuracy': float(row['accuracy']),
                    'speed': float(row['speed']),
                    'personnel_count': int(row['personnel_count'])
                }

                self.logger.debug(
                    f"Loaded type: {type_id} ({row['type_name']}) - "
                    f"HP={row['max_hp']}, Range={row['range']}km, Attack={row['attack_power']}"
                )

            self.logger.info(f"Successfully loaded {len(self.unit_types)} unit types")
            return self.unit_types

        except Exception as e:
            self.logger.error(f"Error loading unit types: {e}", exc_info=True)
            return {}

    def load_objects(self):
        """Load unit instances and combine with type characteristics"""
        try:
            # Step 1: Load unit types
            if not self.unit_types:
                self.load_unit_types()

            if not self.unit_types:
                self.logger.error("No unit types loaded, cannot create instances")
                return []

            # Step 2: Load unit instances
            self.logger.info(f"Loading unit instances from {self.instances_file}")
            df = pd.read_excel(self.instances_file, sheet_name='Units')

            self.units_data = []
            unknown_types = set()

            for _, row in df.iterrows():
                unit_id = int(row['id'])
                type_id = row['type_id']

                # Get characteristics from unit_types
                if type_id not in self.unit_types:
                    if type_id not in unknown_types:
                        self.logger.warning(f"Unknown type_id: {type_id} for unit {unit_id}")
                        unknown_types.add(type_id)
                    continue

                unit_type = self.unit_types[type_id]

                # Combine instance data with type characteristics
                unit_data = {
                    # Instance-specific data
                    'id': unit_id,
                    'type_id': type_id,
                    'side': row['side'],
                    'x_coord': float(row['x_coord']),
                    'y_coord': float(row['y_coord']),
                    'direction': float(row['direction']),

                    # Auto-generated name
                    'name': f"{unit_type['type_name']} #{unit_id}",

                    # Characteristics from unit_types (runtime state)
                    'type': unit_type['class'],
                    'hp': unit_type['max_hp'],  # Start with full HP
                    'max_hp': unit_type['max_hp'],
                    'range': unit_type['range'],
                    'attack_power': unit_type['attack_power'],
                    'accuracy': unit_type['accuracy'],
                    'armor': unit_type['armor'],
                    'speed': unit_type['speed'],
                    'personnel_count': unit_type['personnel_count']
                }

                self.units_data.append(unit_data)

                self.logger.debug(
                    f"Loaded unit: {unit_data['name']} ({unit_data['type']}) - "
                    f"Side {unit_data['side']}, HP={unit_data['hp']}, "
                    f"Range={unit_data['range']}km"
                )

            # Display summary
            side_a = sum(1 for u in self.units_data if u['side'] == 'A')
            side_b = sum(1 for u in self.units_data if u['side'] == 'B')

            self.logger.info(f"Successfully loaded {len(self.units_data)} unit instances")
            self.logger.info(f"  Side A: {side_a} units")
            self.logger.info(f"  Side B: {side_b} units")

            if unknown_types:
                self.logger.warning(f"Skipped {len(unknown_types)} unknown type(s): {unknown_types}")

            # Log unit type distribution
            types_a = {}
            types_b = {}
            for u in self.units_data:
                unit_type = u['type']
                if u['side'] == 'A':
                    types_a[unit_type] = types_a.get(unit_type, 0) + 1
                else:
                    types_b[unit_type] = types_b.get(unit_type, 0) + 1

            self.logger.debug(f"Side A composition: {types_a}")
            self.logger.debug(f"Side B composition: {types_b}")

            return self.units_data

        except Exception as e:
            self.logger.error(f"Error loading unit instances: {e}", exc_info=True)
            return []

    def get_units_by_side(self, side):
        """Get all units for a specific side"""
        return [u for u in self.units_data if u['side'] == side]

    def get_units_by_type(self, unit_type):
        """Get all units of a specific type"""
        return [u for u in self.units_data if u['type'] == unit_type]

    def get_unit_by_id(self, unit_id):
        """Get a specific unit by ID"""
        for unit in self.units_data:
            if unit['id'] == unit_id:
                return unit
        return None

    def display_summary(self):
        """Display summary of loaded units"""
        if not self.units_data:
            print("No units loaded")
            return

        print("\n=== Units Summary ===")
        print(f"Total units: {len(self.units_data)}")

        # Group by side and type
        summary = {}
        for unit in self.units_data:
            side = unit['side']
            unit_type = unit['type']

            if side not in summary:
                summary[side] = {}
            if unit_type not in summary[side]:
                summary[side][unit_type] = 0
            summary[side][unit_type] += 1

        for side in sorted(summary.keys()):
            print(f"\nSide {side}:")
            for unit_type in sorted(summary[side].keys()):
                count = summary[side][unit_type]
                print(f"  {unit_type}: {count}")
