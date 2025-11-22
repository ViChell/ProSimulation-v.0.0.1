import pandas as pd
from .logging_config import SimulationLogger


class DataLoader:
    """Loads military unit data from Excel files"""

    def __init__(self, objects_file='data/objects.xlsx'):
        self.objects_file = objects_file
        self.units_data = []
        self.logger = SimulationLogger.get_logger('data_loader')
    
    def load_objects(self):
        """Load unit objects from Excel file"""
        try:
            self.logger.info(f"Loading units from {self.objects_file}")
            df = pd.read_excel(self.objects_file, sheet_name='Objects')

            self.units_data = []
            for _, row in df.iterrows():
                unit_data = {
                    'id': int(row['ID']),
                    'name': row['Name'],
                    'side': row['Side'],
                    'type': row['Type'],
                    'x_coord': float(row['X_Coord']),
                    'y_coord': float(row['Y_Coord']),
                    'speed': float(row['Speed']),
                    'direction': float(row['Direction']),
                    'hp': float(row['HP']),
                    'max_hp': float(row['Max_HP']),
                    'range': float(row['Range']),
                    'attack_power': float(row['Attack_Power']),
                    'accuracy': float(row['Accuracy']),
                    'armor': float(row['Armor']),
                    'personnel_count': int(row['Personnel_Count'])
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

            self.logger.info(f"Successfully loaded {len(self.units_data)} units")
            self.logger.info(f"  Side A: {side_a} units")
            self.logger.info(f"  Side B: {side_b} units")

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
            self.logger.error(f"Error loading objects: {e}", exc_info=True)
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
