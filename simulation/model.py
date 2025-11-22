import mesa
import logging
from datetime import datetime
from pathlib import Path
from .units import create_unit
from .rules import EngagementRules
from .data_loader import DataLoader
from .logging_config import SimulationLogger, PerformanceTimer
import config


class CombatSimulation(mesa.Model):
    """Main simulation model for combat operations"""
    
    def __init__(self, objects_file='data/objects.xlsx', rules_file='data/sets.xlsx'):
        super().__init__()

        self.step_count = 0
        self.objects_file = objects_file
        self.rules_file = rules_file
        self.combat_events = []  # Події бою для візуалізації

        # Initialize logging system
        if config.LOGGING_ENABLED:
            SimulationLogger.initialize(
                log_dir=config.LOG_DIR,
                log_level=getattr(logging, config.LOG_LEVEL),
                enable_console=config.ENABLE_CONSOLE_OUTPUT,
                enable_combat_log=config.DETAILED_COMBAT_LOG
            )

        self.logger = SimulationLogger.get_logger('model')
        self.combat_logger = SimulationLogger.get_combat_logger() if config.DETAILED_COMBAT_LOG else None
        self.perf_logger = SimulationLogger.get_performance_logger() if config.PERFORMANCE_LOGGING else None

        self.logger.info("="*60)
        self.logger.info("INITIALIZING COMBAT SIMULATION")
        self.logger.info("="*60)
        self.logger.info(f"Objects file: {objects_file}")
        self.logger.info(f"Rules file: {rules_file}")

        # Load engagement rules
        self.engagement_rules = EngagementRules(rules_file)

        # Load unit data and create agents
        self.data_loader = DataLoader(objects_file)
        units_data = self.data_loader.load_objects()

        self.logger.info(f"Loaded {len(units_data)} units")
        side_a_count = len([u for u in units_data if u['side'] == 'A'])
        side_b_count = len([u for u in units_data if u['side'] == 'B'])
        self.logger.info(f"Side A: {side_a_count} units | Side B: {side_b_count} units")

        # Create military units
        for unit_data in units_data:
            unit = create_unit(self, unit_data)
            self.agents.add(unit)
            self.logger.debug(f"Created unit: {unit.name} ({unit.unit_type}) - Side {unit.side} at {unit.pos}")

        self.logger.info(f"Simulation initialized with {len(self.agents)} units")
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

        self.logger.info("="*60)
        self.logger.info(f"STEP {self.step_count}")
        self.logger.info("="*60)

        # Performance timing
        if self.perf_logger:
            perf_timer = PerformanceTimer(self.perf_logger, f"Step {self.step_count}")
            perf_timer.__enter__()
        else:
            perf_timer = None

        # Shuffle and execute step for each agent
        agents_list = list(self.agents)
        self.random.shuffle(agents_list)

        for agent in agents_list:
            agent.step()

        # Stop performance timer
        if perf_timer:
            perf_timer.__exit__(None, None, None)

        # Calculate statistics
        shots = len([e for e in self.combat_events if e['type'] == 'shot'])
        hits = len([e for e in self.combat_events if e['type'] == 'hit'])
        kills = len([e for e in self.combat_events if e['type'] == 'destroyed'])

        side_a_alive = len([a for a in self.agents if a.side == 'A' and a.is_alive])
        side_b_alive = len([a for a in self.agents if a.side == 'B' and a.is_alive])

        self.logger.info(f"Combat events: {shots} shots, {hits} hits, {kills} destroyed")
        self.logger.info(f"Forces alive - Side A: {side_a_alive} | Side B: {side_b_alive}")

        # Check if simulation should continue
        if side_a_alive == 0 or side_b_alive == 0:
            self.running = False
            winner = 'Side B' if side_a_alive == 0 else 'Side A'

            self.logger.info("="*60)
            self.logger.critical(f"SIMULATION ENDED AT STEP {self.step_count}")
            self.logger.critical(f"WINNER: {winner}")
            self.logger.info("="*60)

            # Детальна статистика
            self.print_final_statistics()

            # Автоматичний аналіз логів після завершення
            self.run_post_simulation_analysis()

    def print_final_statistics(self):
        """Print detailed end-of-battle statistics"""
        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("="*60)

        for side in ['A', 'B']:
            units = [a for a in self.agents if a.side == side]
            alive = [a for a in units if a.is_alive]
            total_kills = sum(u.kills for u in units)
            total_shots = sum(u.shots_fired for u in units)
            total_hits = sum(u.hits_landed for u in units)
            accuracy = (total_hits / total_shots * 100) if total_shots > 0 else 0

            self.logger.info("")
            self.logger.info(f"Side {side}:")
            self.logger.info(f"  Survived: {len(alive)}/{len(units)}")
            self.logger.info(f"  Total kills: {total_kills}")
            self.logger.info(f"  Total shots: {total_shots}, Hits: {total_hits}")
            self.logger.info(f"  Overall accuracy: {accuracy:.1f}%")

            # Top killers
            top_killers = sorted(units, key=lambda u: u.kills, reverse=True)[:3]
            if any(u.kills > 0 for u in top_killers):
                self.logger.info("  Top performers:")
                for u in top_killers:
                    if u.kills > 0:
                        unit_accuracy = (u.hits_landed / u.shots_fired * 100) if u.shots_fired > 0 else 0
                        self.logger.info(f"    - {u.name}: {u.kills} kills, {unit_accuracy:.1f}% accuracy ({u.hits_landed}/{u.shots_fired})")

        self.logger.info("="*60)

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
        self.logger.info(f"Current simulation status at step {self.step_count}")

        for side in ['A', 'B']:
            units = [a for a in self.agents if a.side == side]
            alive = [a for a in units if a.is_alive]
            total_kills = sum(a.kills for a in units)
            total_shots = sum(a.shots_fired for a in units)
            total_hits = sum(a.hits_landed for a in units)
            accuracy = (total_hits / total_shots * 100) if total_shots > 0 else 0

            self.logger.info(f"Side {side}: {len(alive)}/{len(units)} alive, {total_kills} kills, {accuracy:.1f}% accuracy")
    
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

    def run_post_simulation_analysis(self):
        """Запустити автоматичний аналіз логів після завершення симуляції"""
        try:
            # Імпортувати аналізатор
            import sys
            from pathlib import Path
            tools_path = Path(__file__).parent.parent / 'tools'
            if str(tools_path) not in sys.path:
                sys.path.insert(0, str(tools_path))

            from log_analyzer import analyze_latest_log

            # Генерувати ім'я файлу з timestamp
            timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
            output_file = Path(config.LOG_DIR) / f'analysis_{timestamp}.txt'

            self.logger.info("="*60)
            self.logger.info("RUNNING POST-SIMULATION ANALYSIS")
            self.logger.info("="*60)
            self.logger.info(f"Analysis output: {output_file}")

            # Запустити аналіз
            success = analyze_latest_log(output_txt=str(output_file))

            if success:
                self.logger.info(f"Analysis completed successfully: {output_file}")
            else:
                self.logger.warning("Analysis failed or produced no output")

        except Exception as e:
            self.logger.error(f"Error running post-simulation analysis: {e}", exc_info=True)
