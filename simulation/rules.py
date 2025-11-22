import pandas as pd
from .logging_config import SimulationLogger


class EngagementRules:
    """Manages combat engagement rules loaded from Excel"""

    def __init__(self, filepath='data/sets.xlsx'):
        self.filepath = filepath
        self.rules = {}
        self.modifiers = {}
        self.logger = SimulationLogger.get_logger('rules')
        self.load_rules()
    
    def load_rules(self):
        """Load engagement rules from Excel file"""
        try:
            self.logger.info(f"Loading engagement rules from {self.filepath}")

            # Load engagement rules
            rules_df = pd.read_excel(self.filepath, sheet_name='Engagement_Rules')

            for _, row in rules_df.iterrows():
                attacker = row['Attacker_Type']
                target = row['Target_Type']

                key = (attacker, target)
                self.rules[key] = {
                    'base_hit_probability': row['Base_Hit_Probability'],
                    'damage_multiplier': row['Damage_Multiplier'],
                    'min_range': row['Min_Range'],
                    'max_range': row['Max_Range'],
                    'priority': row['Engagement_Priority'],
                    'notes': row['Notes']
                }

                self.logger.debug(
                    f"Rule: {attacker} -> {target}: "
                    f"hit={row['Base_Hit_Probability']:.2f}, "
                    f"dmg={row['Damage_Multiplier']:.2f}, "
                    f"range=[{row['Min_Range']:.1f}-{row['Max_Range']:.1f}]"
                )

            # Load combat modifiers
            try:
                modifiers_df = pd.read_excel(self.filepath, sheet_name='Combat_Modifiers', skiprows=1)
                for _, row in modifiers_df.iterrows():
                    modifier_key = (row['Modifier_Type'], row['Condition'])
                    self.modifiers[modifier_key] = {
                        'multiplier': row['Effect_Multiplier'],
                        'description': row['Description']
                    }
                self.logger.info(f"Loaded {len(self.modifiers)} combat modifiers")
            except Exception as e:
                self.logger.warning(f"Combat_Modifiers sheet not found or could not be loaded: {e}")

            self.logger.info(f"Successfully loaded {len(self.rules)} engagement rules")

        except Exception as e:
            self.logger.error(f"Error loading engagement rules: {e}", exc_info=True)
            self.rules = {}
            self.modifiers = {}
    
    def get_rule(self, attacker_type, target_type):
        """Get engagement rule for attacker-target pair"""
        return self.rules.get((attacker_type, target_type))
    
    def get_priority(self, attacker_type, target_type):
        """Get engagement priority (lower is higher priority)"""
        rule = self.get_rule(attacker_type, target_type)
        return rule['priority'] if rule else 999
    
    def get_modifier(self, modifier_type, condition):
        """Get combat modifier"""
        return self.modifiers.get((modifier_type, condition))
    
    def can_engage(self, attacker_type, target_type, distance):
        """Check if attacker can engage target at given distance"""
        rule = self.get_rule(attacker_type, target_type)
        if not rule:
            return False
        
        return rule['min_range'] <= distance <= rule['max_range']
    
    def get_all_attacker_rules(self, attacker_type):
        """Get all rules for a specific attacker type"""
        return {target: rule for (att, target), rule in self.rules.items() if att == attacker_type}
    
    def get_all_target_rules(self, target_type):
        """Get all rules where unit type is targeted"""
        return {attacker: rule for (attacker, tgt), rule in self.rules.items() if tgt == target_type}
    
    def display_rules_summary(self):
        """Display summary of engagement rules"""
        unit_types = set()
        for attacker, target in self.rules.keys():
            unit_types.add(attacker)
            unit_types.add(target)
        
        print("\n=== Engagement Rules Summary ===")
        print(f"Unit types: {sorted(unit_types)}")
        print(f"Total engagement rules: {len(self.rules)}")
        print(f"Combat modifiers: {len(self.modifiers)}")
        
        print("\n=== Rules Matrix ===")
        unit_types_list = sorted(unit_types)
        
        # Print header
        print(f"{'Attacker':<15}", end="")
        for target in unit_types_list:
            print(f"{target:<10}", end="")
        print()
        
        # Print rules
        for attacker in unit_types_list:
            print(f"{attacker:<15}", end="")
            for target in unit_types_list:
                rule = self.get_rule(attacker, target)
                if rule:
                    prob = rule['base_hit_probability']
                    print(f"{prob:<10.2f}", end="")
                else:
                    print(f"{'---':<10}", end="")
            print()
