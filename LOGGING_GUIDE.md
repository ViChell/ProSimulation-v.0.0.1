# Система логування Combat Simulation

## 📝 Огляд

Система симуляції бойових дій використовує **асинхронне логування** для мінімізації впливу на продуктивність. Всі логи записуються на диск в окремих потоках через систему черг.

## 🏗️ Архітектура

### Компоненти системи

1. **SimulationLogger** - Централізована фабрика логерів
   - Використовує `QueueHandler` для асинхронного запису
   - Підтримує різні рівні логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Автоматично створює директорії та файли

2. **AsyncCombatLogger** - Спеціалізований логер для бойових подій
   - Записує події в JSON формат (1 подія = 1 рядок)
   - Працює в окремому потоці
   - Мінімальний overhead (~0.1-0.5ms на подію)

3. **PerformanceTimer** - Context manager для вимірювання часу виконання

## 📂 Структура логів

```
logs/
├── simulation/              # Основні логи симуляції
│   ├── simulation_2025-01-22_14-30-45.log
│   └── simulation_latest.log
├── combat/                  # Детальні події бою (JSON)
│   ├── combat_2025-01-22_14-30-45.json
│   ├── combat_2025-01-22_14-30-45_summary.json
│   └── combat_latest.json
├── errors/                  # Помилки та виключення
│   └── errors_2025-01-22.log
└── performance/            # Метрики продуктивності
    └── performance_2025-01-22_14-30-45.log
```

## ⚙️ Конфігурація

### config.py

```python
# Logging configuration
LOGGING_ENABLED = True              # Увімкнути/вимкнути логування
LOG_DIR = 'logs'                    # Директорія для логів
LOG_LEVEL = 'INFO'                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENABLE_CONSOLE_OUTPUT = False       # Виводити в консоль (може сповільнити)
DETAILED_COMBAT_LOG = True          # JSON лог бойових подій
PERFORMANCE_LOGGING = False         # Логування метрик продуктивності
```

### Рівні логування

| Рівень | Що логується | Приклади |
|--------|--------------|----------|
| **DEBUG** | Детальна інформація | Пошук цілей, розрахунки дистанцій, промахи |
| **INFO** | Основні події | Початок кроку, влучення, статистика |
| **WARNING** | Важливі події | Знищення юнітів, відсутні правила |
| **ERROR** | Помилки | Не вдалось завантажити файл |
| **CRITICAL** | Критичні події | Завершення симуляції |

## 📊 Формати логів

### 1. Simulation Log (simulation_*.log)

Текстовий формат з повною інформацією:

```
2025-01-22 14:30:45 - combat_sim.model - INFO - [model.py:76] STEP 1
2025-01-22 14:30:45 - combat_sim.units - DEBUG - [units.py:68] Tank_A1 acquired target: BMP_B2 (distance: 1.25km, priority: 2)
2025-01-22 14:30:46 - combat_sim.units - INFO - [units.py:159] HIT! Tank_A1 -> BMP_B2: 45.3 damage (roll: 0.230 < 0.750)
2025-01-22 14:30:46 - combat_sim.units - WARNING - [units.py:185] DESTROYED! Tank_A1 destroyed BMP_B2 (total kills: 1)
```

### 2. Combat Log (combat_*.json)

JSON формат для аналізу (1 подія = 1 рядок):

```json
{"timestamp": "2025-01-22T14:30:45.123456", "step": 1, "event_type": "shot", "attacker": {"id": 101, "name": "Tank_A1", "type": "tank", "side": "A", "position": [36.3, 47.6]}, "target": {"id": 201, "name": "BMP_B2", "type": "bmp", "side": "B", "position": [36.32, 47.62], "hp": 80, "max_hp": 100}, "distance": 1.25, "hit_chance": 0.75}
{"timestamp": "2025-01-22T14:30:45.123789", "step": 1, "event_type": "hit", "attacker": {...}, "target": {...}, "damage": 45.3, "raw_damage": 50.0, "armor_reduction": 4.7}
{"timestamp": "2025-01-22T14:30:45.124012", "step": 1, "event_type": "destroyed", "attacker": {...}, "target": {...}, "total_kills": 1}
```

### 3. Error Log (errors_*.log)

Тільки помилки з повним stack trace:

```
2025-01-22 14:30:45 - combat_sim.rules - ERROR - [rules.py:60] Error loading engagement rules: [Errno 2] No such file or directory: 'data/sets.xlsx'
Traceback (most recent call last):
  File "rules.py", line 18, in load_rules
    rules_df = pd.read_excel(self.filepath, sheet_name='Engagement_Rules')
  ...
```

## 🔍 Аналіз логів

### Використання log_analyzer.py

```bash
# Аналізувати конкретний файл
python tools/log_analyzer.py logs/combat/combat_2025-01-22_14-30-45.json

# Аналізувати останній лог (автоматичний пошук)
python tools/log_analyzer.py
```

### Приклад виводу

```
======================================================================
                     COMBAT LOG ANALYSIS
======================================================================

📊 GENERAL STATISTICS
----------------------------------------------------------------------
Total events:        1523
Total steps:         45

Events by type:
  destroyed      :     12
  hit            :    245
  shot           :   1266

🎯 STATISTICS BY SIDE
----------------------------------------------------------------------

Side A:
  Shots fired:     687
  Hits landed:     134
  Accuracy:        19.5%
  Enemy destroyed: 7

Side B:
  Shots fired:     579
  Hits landed:     111
  Accuracy:        19.2%
  Enemy destroyed: 5

🔫 STATISTICS BY UNIT TYPE
----------------------------------------------------------------------
Type            Shots     Hits    Kills  Accuracy
----------------------------------------------------------------------
artillery          89       18        2      20.2%
bmp               234       45        3      19.2%
infantry          456       87        4      19.1%
tank              487       95        3      19.5%

🏆 TOP PERFORMERS
----------------------------------------------------------------------
Rank   Name                 Type       Side   Kills   Acc%
----------------------------------------------------------------------
1      Tank_A1              tank       A          3   24.5%
2      Artillery_B5         artillery  B          2   22.2%
3      BMP_A3               bmp        A          2   21.1%
```

### Експорт статистики

Аналізатор автоматично створює файл `*_analysis.json` з детальною статистикою:

```json
{
  "total_events": 1523,
  "by_type": {
    "shot": 1266,
    "hit": 245,
    "destroyed": 12
  },
  "by_side": {
    "A": {
      "shots": 687,
      "hits": 134,
      "destroyed": 0,
      "kills": 7
    }
  },
  ...
}
```

## 🚀 Продуктивність

### Overhead логування

| Конфігурація | Overhead на 1000 юнітів |
|--------------|-------------------------|
| `LOG_LEVEL=INFO` + async | ~10-30ms/крок |
| `LOG_LEVEL=DEBUG` + async | ~50-150ms/крок |
| Без логування | 0ms |

### Рекомендації

**Для розробки:**
```python
LOG_LEVEL = 'DEBUG'
DETAILED_COMBAT_LOG = True
PERFORMANCE_LOGGING = True
```

**Для великих симуляцій (1000+ юнітів):**
```python
LOG_LEVEL = 'INFO'
DETAILED_COMBAT_LOG = True
PERFORMANCE_LOGGING = False
ENABLE_CONSOLE_OUTPUT = False  # Важливо!
```

**Для максимальної швидкості:**
```python
LOG_LEVEL = 'WARNING'
DETAILED_COMBAT_LOG = False
PERFORMANCE_LOGGING = False
```

## 📖 Приклади використання

### Програмний доступ до логів

```python
from simulation.logging_config import SimulationLogger

# Отримати логер
logger = SimulationLogger.get_logger('my_module')

# Логування
logger.debug("Детальна інформація")
logger.info("Загальна інформація")
logger.warning("Попередження")
logger.error("Помилка")
logger.critical("Критична помилка")

# Combat logger
combat_logger = SimulationLogger.get_combat_logger()
if combat_logger:
    combat_logger.log_event('shot', step, attacker, target, distance=1.5)

# Performance timing
from simulation.logging_config import PerformanceTimer

perf_logger = SimulationLogger.get_performance_logger()
with PerformanceTimer(perf_logger, "My operation"):
    # Ваш код
    ...
```

### Читання JSON логів

```python
import json

with open('logs/combat/combat_latest.json', 'r') as f:
    for line in f:
        event = json.loads(line)
        print(f"{event['event_type']}: {event['attacker']['name']} -> {event['target']['name']}")
```

## 🛠️ Налагодження

### Проблема: Логи не створюються

1. Перевірте `config.py`:
   ```python
   LOGGING_ENABLED = True
   ```

2. Перевірте права на запис в директорію `logs/`

3. Перевірте консоль на помилки ініціалізації

### Проблема: Симуляція працює повільно

1. Вимкніть консольний вивід:
   ```python
   ENABLE_CONSOLE_OUTPUT = False
   ```

2. Зменшіть рівень логування:
   ```python
   LOG_LEVEL = 'INFO'  # замість DEBUG
   ```

3. Вимкніть performance logging:
   ```python
   PERFORMANCE_LOGGING = False
   ```

### Проблема: Забагато логів на диску

Логи автоматично ротуються:
- Simulation log: максимум 10MB, 5 backup файлів (50MB всього)
- Combat JSON: необмежений (видаляйте старі вручну)
- Error log: один файл на день

## 📚 Додаткова інформація

### Структура події combat log

```python
{
    'timestamp': str,        # ISO формат
    'step': int,            # Номер кроку
    'event_type': str,      # 'shot', 'hit', 'destroyed'
    'attacker': {
        'id': int,
        'name': str,
        'type': str,
        'side': str,
        'position': [float, float]
    },
    'target': {
        'id': int,
        'name': str,
        'type': str,
        'side': str,
        'position': [float, float],
        'hp': float,
        'max_hp': float
    },
    # Додаткові поля залежно від event_type:
    'distance': float,       # для 'shot'
    'hit_chance': float,     # для 'shot'
    'damage': float,         # для 'hit'
    'raw_damage': float,     # для 'hit'
    'armor_reduction': float,# для 'hit'
    'total_kills': int       # для 'destroyed'
}
```

## 🤝 Внесок

При додаванні нового функціоналу:

1. Використовуйте відповідний рівень логування
2. Логуйте важливі події
3. Додавайте контекст (імена юнітів, значення параметрів)
4. Використовуйте combat logger для подій бою

## 📄 Ліцензія

Частина проекту Combat Simulation System
