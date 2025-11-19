#!/usr/bin/env python3
"""
Test script for Combat Simulation System
Verifies data loading and basic simulation functionality
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.data_loader import DataLoader
from simulation.rules import EngagementRules
from simulation.model import CombatSimulation


def test_data_loading():
    """Test loading data from Excel files"""
    print("=" * 60)
    print("TEST 1: Data Loading")
    print("=" * 60)
    
    # Test objects loading
    print("\n--- Loading objects.xlsx ---")
    loader = DataLoader('data/objects.xlsx')
    units = loader.load_objects()
    loader.display_summary()
    
    # Test rules loading
    print("\n--- Loading sets.xlsx ---")
    rules = EngagementRules('data/sets.xlsx')
    rules.display_rules_summary()
    
    print("\n✓ Data loading test passed")
    return True


def test_simulation_init():
    """Test simulation initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: Simulation Initialization")
    print("=" * 60)
    
    sim = CombatSimulation('data/objects.xlsx', 'data/sets.xlsx')
    print("\n✓ Simulation initialization test passed")
    return sim


def test_simulation_steps(sim, steps=5):
    """Test running simulation for a few steps"""
    print("\n" + "=" * 60)
    print(f"TEST 3: Running {steps} Simulation Steps")
    print("=" * 60)
    
    for i in range(steps):
        print(f"\n--- Step {i+1} ---")
        sim.step()
        
        # Show some statistics
        stats = sim.get_statistics()
        print(f"Side A: {stats['sides']['A']['alive']}/{stats['sides']['A']['total_units']} alive")
        print(f"Side B: {stats['sides']['B']['alive']}/{stats['sides']['B']['total_units']} alive")
        
        if not sim.running:
            print("\nSimulation ended!")
            break
    
    print("\n✓ Simulation steps test passed")
    return True


def test_engagement_rules():
    """Test specific engagement rules"""
    print("\n" + "=" * 60)
    print("TEST 4: Engagement Rules")
    print("=" * 60)
    
    rules = EngagementRules('data/sets.xlsx')
    
    # Test specific rule
    print("\n--- Tank vs Tank engagement ---")
    rule = rules.get_rule('tank', 'tank')
    if rule:
        print(f"Base Hit Probability: {rule['base_hit_probability']}")
        print(f"Damage Multiplier: {rule['damage_multiplier']}")
        print(f"Range: {rule['min_range']} - {rule['max_range']} km")
        print(f"Priority: {rule['priority']}")
    
    # Test infantry vs tank
    print("\n--- Infantry vs Tank engagement ---")
    rule = rules.get_rule('infantry', 'tank')
    if rule:
        print(f"Base Hit Probability: {rule['base_hit_probability']}")
        print(f"Damage Multiplier: {rule['damage_multiplier']}")
        print(f"Range: {rule['min_range']} - {rule['max_range']} km")
        print(f"Notes: {rule['notes']}")
    
    print("\n✓ Engagement rules test passed")
    return True


def test_geojson_export(sim):
    """Test GeoJSON export"""
    print("\n" + "=" * 60)
    print("TEST 5: GeoJSON Export")
    print("=" * 60)
    
    geojson = sim.get_state()
    print(f"\nTotal features: {len(geojson['features'])}")
    
    # Show first unit
    if geojson['features']:
        first_unit = geojson['features'][0]
        print("\nFirst unit properties:")
        for key, value in first_unit['properties'].items():
            print(f"  {key}: {value}")
    
    print("\n✓ GeoJSON export test passed")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMBAT SIMULATION SYSTEM - TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Data Loading
        if not test_data_loading():
            return False
        
        # Test 2: Simulation Initialization
        sim = test_simulation_init()
        if not sim:
            return False
        
        # Test 3: Engagement Rules
        if not test_engagement_rules():
            return False
        
        # Test 4: Simulation Steps
        if not test_simulation_steps(sim, steps=3):
            return False
        
        # Test 5: GeoJSON Export
        if not test_geojson_export(sim):
            return False
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
        # Final statistics
        print("\n--- Final Statistics ---")
        sim.display_status()
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
