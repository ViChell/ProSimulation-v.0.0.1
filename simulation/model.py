import mesa
from .units import create_unit
from .rules import EngagementRules
from .data_loader import DataLoader


class CombatSimulation(mesa.Model):
    """Main simulation model for combat operations"""
    
    def __init__(self, objects_file='data/objects.xlsx', rules_file='data/sets.xlsx'):
        super().__init__()
        
        self.step_count = 0
        self.objects_file = objects_file
        self.rules_file = rules_file
        self.combat_events = []  # Події бою для візуалізації
        
        # Load engagement rules
        self.engagement_rules = EngagementRules(rules_file)
        
        # Load unit data and create agents
        self.data_loader = DataLoader(objects_file)
        units_data = self.data_loader.load_objects()
        
        # Create military units
        for unit_data in units_data:
            unit = create_unit(self, unit_data)
            self.agents.add(unit)
        
        print(f"\nSimulation initialized with {len(self.agents)} units")
        self.display_status()
    
    def get_engagement_rule(self, attacker_type, target_type):
        """Get engagement rule from rules manager"""
        return self.engagement_rules.get_rule(attacker_type, target_type)
    
    def get_engagement_priority(self, attacker_type, target_type):
        """Get engagement priority"""
        return self.engagement_rules.get_priority(attacker_type, target_type)
    
    def step(self):
        """Execute one step of the simulation"""
        self.step_count += 1
        
        # Очистити події попереднього кроку
        self.combat_events = []

        print(f"\n=== Step {self.step_count} ===")

        # Shuffle and execute step for each agent
        agents_list = list(self.agents)
        self.random.shuffle(agents_list)
        for agent in agents_list:
            agent.step()

        shots = len([e for e in self.combat_events if e['type'] == 'shot'])
        hits = len([e for e in self.combat_events if e['type'] == 'hit'])
        kills = len([e for e in self.combat_events if e['type'] == 'destroyed'])
        
        print(f"Shots: {shots}, Hits: {hits}, Kills: {kills}")
        print(f"Side A: {len([a for a in self.agents if a.side == 'A' and a.is_alive])} alive")
        print(f"Side B: {len([a for a in self.agents if a.side == 'B' and a.is_alive])} alive")    
        
        # Check if simulation should continue
        side_a_alive = any(agent.is_alive and agent.side == 'A' for agent in self.agents)
        side_b_alive = any(agent.is_alive and agent.side == 'B' for agent in self.agents)
        
        if not side_a_alive or not side_b_alive:
            self.running = False
            print(f"\n=== Simulation ended at step {self.step_count} ===")
            if not side_a_alive:
                print("Side B VICTORY")
            else:
                print("Side A VICTORY")    
        
        if not side_a_alive or not side_b_alive:
            self.running = False
            print(f"\n{'='*60}")
            print(f"SIMULATION ENDED AT STEP {self.step_count}")
            print(f"{'='*60}")
            
            winner = 'Side B' if not side_a_alive else 'Side A'
            print(f"WINNER: {winner}\n")
            
            # Детальна статистика
            self.print_final_statistics()

    def print_final_statistics(self):
        """Print detailed end-of-battle statistics"""
        print("\n=== FINAL STATISTICS ===\n")
        
        for side in ['A', 'B']:
            units = [a for a in self.agents if a.side == side]
            alive = [a for a in units if a.is_alive]
            
            print(f"Side {side}:")
            print(f"  Survived: {len(alive)}/{len(units)}")
            print(f"  Total kills: {sum(u.kills for u in units)}")
            print(f"  Total shots: {sum(u.shots_fired for u in units)}")
            print(f"  Total hits: {sum(u.hits_landed for u in units)}")
            
            # Top killers
            top_killers = sorted(units, key=lambda u: u.kills, reverse=True)[:3]
            print(f"  Top killers:")
            for u in top_killers:
                if u.kills > 0:
                    print(f"    - {u.name}: {u.kills} kills, {u.hits_landed}/{u.shots_fired} accuracy")
            print()

    # Метод для логування подій:
    def log_combat_event(self, event_type, attacker, target, success=False):
        """Log combat event for visualization"""
        self.combat_events.append({
            'type': event_type,  # 'shot', 'hit', 'destroyed'
            'attacker_id': attacker.unit_id,
            'attacker_pos': list(attacker.pos),
            'target_id': target.unit_id,
            'target_pos': list(target.pos),
            'success': success,
            'timestamp': self.step_count
        })

    def get_state(self):
        """Get current state of all units in GeoJSON format"""
        features = []
        
        for agent in self.agents:
            if not agent.is_alive:
                continue

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [agent.pos[0], agent.pos[1]]
                },
                'properties': {
                    'id': agent.unit_id,
                    'name': agent.name,
                    'side': agent.side,
                    'type': agent.unit_type,
                    'hp': agent.hp,
                    'max_hp': agent.max_hp,
                    'hp_percent': round((agent.hp / agent.max_hp) * 100, 1),
                    'kills': agent.kills,
                    'shots_fired': agent.shots_fired,
                    'hits_landed': agent.hits_landed,
                    'accuracy_percent': round((agent.hits_landed / agent.shots_fired * 100) 
                                            if agent.shots_fired > 0 else 0, 1),
                    'personnel_count': agent.personnel_count,
                    'has_target': agent.target is not None and agent.target.is_alive,
                    'is_alive': agent.is_alive  # ДОДАТИ ЦЕ
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'events': self.combat_events 
        }
    
    def get_casualties(self):
        """Get casualty statistics"""
        stats = {
            'A': {'total': 0, 'destroyed': 0, 'damaged': 0, 'by_type': {}},
            'B': {'total': 0, 'destroyed': 0, 'damaged': 0, 'by_type': {}}
        }
        
        for agent in self.agents:
            side = agent.side
            unit_type = agent.unit_type
            
            stats[side]['total'] += 1
            
            if unit_type not in stats[side]['by_type']:
                stats[side]['by_type'][unit_type] = {
                    'total': 0, 'destroyed': 0, 'damaged': 0
                }
            
            stats[side]['by_type'][unit_type]['total'] += 1
            
            if not agent.is_alive:
                stats[side]['destroyed'] += 1
                stats[side]['by_type'][unit_type]['destroyed'] += 1
            elif agent.hp < agent.max_hp:
                stats[side]['damaged'] += 1
                stats[side]['by_type'][unit_type]['damaged'] += 1
        
        return stats
    
    def display_status(self):
        """Display current simulation status"""
        print(f"\n=== Step {self.step_count} ===")
        
        for side in ['A', 'B']:
            units = [a for a in self.agents if a.side == side]
            alive = [a for a in units if a.is_alive]
            total_kills = sum(a.kills for a in units)
            total_shots = sum(a.shots_fired for a in units)
            total_hits = sum(a.hits_landed for a in units)
            
            print(f"\nSide {side}:")
            print(f"  Alive: {len(alive)}/{len(units)}")
            print(f"  Kills: {total_kills}")
            print(f"  Shots: {total_shots}, Hits: {total_hits}")
            if total_shots > 0:
                print(f"  Overall Accuracy: {(total_hits/total_shots*100):.1f}%")
    
    def get_statistics(self):
        """Get detailed statistics for the simulation"""
        stats = {
            'step': self.step_count,
            'sides': {}
        }
        
        for side in ['A', 'B']:
            units = [a for a in self.agents if a.side == side]
            alive_units = [a for a in units if a.is_alive]
            
            side_stats = {
                'total_units': len(units),
                'alive': len(alive_units),
                'destroyed': len(units) - len(alive_units),
                'total_kills': sum(a.kills for a in units),
                'total_shots': sum(a.shots_fired for a in units),
                'total_hits': sum(a.hits_landed for a in units),
                'accuracy': round((sum(a.hits_landed for a in units) / 
                                  sum(a.shots_fired for a in units) * 100) 
                                 if sum(a.shots_fired for a in units) > 0 else 0, 2),
                'by_type': {}
            }
            
            # Statistics by unit type
            unit_types = set(a.unit_type for a in units)
            for unit_type in unit_types:
                type_units = [a for a in units if a.unit_type == unit_type]
                type_alive = [a for a in type_units if a.is_alive]
                
                side_stats['by_type'][unit_type] = {
                    'total': len(type_units),
                    'alive': len(type_alive),
                    'destroyed': len(type_units) - len(type_alive),
                    'kills': sum(a.kills for a in type_units)
                }
            
            stats['sides'][side] = side_stats
        
        return stats
