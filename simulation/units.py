import mesa
import math
import random


class MilitaryUnit(mesa.Agent):
    """Base class for all military units"""
    
    def __init__(self, model, unit_id, name, side, unit_type, pos, speed, direction,
                 hp, max_hp, attack_range, attack_power, accuracy, armor, personnel_count=0):
        super().__init__(unit_id, model)
        self.unit_id = unit_id
        self.name = name
        self.side = side
        self.unit_type = unit_type
        self.pos = pos
        self.speed = speed
        self.direction = direction
        self.hp = hp
        self.max_hp = max_hp
        self.attack_range = attack_range
        self.attack_power = attack_power
        self.accuracy = accuracy
        self.armor = armor
        self.personnel_count = personnel_count
        
        self.target = None
        self.is_alive = True
        self.kills = 0
        self.shots_fired = 0
        self.hits_landed = 0
        
    def calculate_distance(self, other_pos):
        """Calculate distance to another position in km (approximate)"""
        dx = (other_pos[0] - self.pos[0]) * 111.32  # lon to km at equator
        dy = (other_pos[1] - self.pos[1]) * 110.54  # lat to km
        return math.sqrt(dx**2 + dy**2)
    
    def find_target(self):
        """Find closest enemy within range"""
        enemies = [agent for agent in self.model.agents 
                   if agent.side != self.side and agent.is_alive]
        
        if not enemies:
            return None
        
        # Filter by range and sort by priority and distance
        valid_targets = []
        for enemy in enemies:
            distance = self.calculate_distance(enemy.pos)
            if distance <= self.attack_range:
                priority = self.model.get_engagement_priority(self.unit_type, enemy.unit_type)
                valid_targets.append((enemy, distance, priority))
        
        if not valid_targets:
            return None
        
        # Sort by priority (lower is better) then distance
        valid_targets.sort(key=lambda x: (x[2], x[1]))
        return valid_targets[0][0]
    
    def move_towards_enemy(self):
        """Move towards nearest enemy"""
        enemies = [agent for agent in self.model.agents 
                   if agent.side != self.side and agent.is_alive]
        
        if not enemies:
            return
        
        # Find nearest enemy
        nearest_enemy = min(enemies, key=lambda e: self.calculate_distance(e.pos))
        target_pos = nearest_enemy.pos
        
        # Calculate direction
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            # Move towards target
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
            
            # Update direction
            self.direction = math.degrees(math.atan2(dy, dx))
    
    def attack(self, target):
        """Attempt to attack target"""
        if not target or not target.is_alive:
            return False
        
        distance = self.calculate_distance(target.pos)
        
        # Check if target is in range
        engagement_rule = self.model.get_engagement_rule(self.unit_type, target.unit_type)
        if not engagement_rule:
            return False
        
        min_range = engagement_rule.get('min_range', 0)
        max_range = engagement_rule.get('max_range', self.attack_range)
        
        if distance < min_range or distance > max_range:
            return False
        
        self.shots_fired += 1

        # Логування пострілу
        self.model.log_combat_event('shot', self, target, False)

        # Calculate hit probability
        base_probability = engagement_rule.get('base_hit_probability', 0.5)
        hit_chance = base_probability * self.accuracy
        
        # Roll for hit
        if random.random() < hit_chance:
            self.hits_landed += 1
            
            # Calculate damage
            damage_multiplier = engagement_rule.get('damage_multiplier', 1.0)
            raw_damage = self.attack_power * damage_multiplier
            
            # Apply armor reduction
            armor_reduction = target.armor * 0.5
            final_damage = max(0, raw_damage - armor_reduction)

            # Логування влучення
            self.model.log_combat_event('hit', self, target, True)
            
            # Apply damage
            target.take_damage(final_damage)
            
            if not target.is_alive:
                self.kills += 1
                # Логування знищення
                self.model.log_combat_event('destroyed', self, target, True)
            
            return True
        
        return False
    
    def take_damage(self, damage):
        """Take damage from attack"""
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
    
    def step(self):
        """Execute one step of behavior"""
        if not self.is_alive:
            return
        
        # Find and engage target
        if self.target is None or not self.target.is_alive:
            self.target = self.find_target()
        
        if self.target:
            # Try to attack
            self.attack(self.target)
        else:
            # No target in range, move towards enemies
            self.move_towards_enemy()


class Tank(MilitaryUnit):
    """Tank unit - heavy armor, main battle tank"""
    pass


class BMP(MilitaryUnit):
    """BMP/IFV unit - infantry fighting vehicle"""
    pass


class Infantry(MilitaryUnit):
    """Infantry squad unit"""
    pass


class Mortar(MilitaryUnit):
    """Mortar unit - indirect fire support"""
    pass


class Artillery(MilitaryUnit):
    """Artillery unit - long range fire support"""
    pass


class UAV(MilitaryUnit):
    """UAV unit - reconnaissance and strike"""
    pass


def create_unit(model, unit_data):
    """Factory function to create appropriate unit type"""
    unit_type = unit_data['type'].lower()
    
    common_args = {
        'model': model,
        'unit_id': unit_data['id'],
        'name': unit_data['name'],
        'side': unit_data['side'],
        'unit_type': unit_type,
        'pos': (unit_data['x_coord'], unit_data['y_coord']),
        'speed': unit_data['speed'],
        'direction': unit_data['direction'],
        'hp': unit_data['hp'],
        'max_hp': unit_data['max_hp'],
        'attack_range': unit_data['range'],
        'attack_power': unit_data['attack_power'],
        'accuracy': unit_data['accuracy'],
        'armor': unit_data['armor'],
        'personnel_count': unit_data['personnel_count']
    }
    
    unit_classes = {
        'tank': Tank,
        'bmp': BMP,
        'infantry': Infantry,
        'mortar': Mortar,
        'artillery': Artillery,
        'uav': UAV
    }
    
    unit_class = unit_classes.get(unit_type, MilitaryUnit)
    return unit_class(**common_args)
