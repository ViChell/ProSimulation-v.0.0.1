# RL Implementation Summary

## Що було додано

Система навчання з підкріпленням (Reinforcement Learning) для Combat Simulation.

## Структура файлів

### Нові файли

```
__ProMesa_combat_simulation/
├── simulation/rl/                    # Головний RL модуль
│   ├── __init__.py                   # Експорти модуля
│   ├── environment.py                # Gymnasium environment
│   ├── observation.py                # Observation space builder
│   ├── actions.py                    # Action space handler
│   ├── rewards.py                    # Reward calculator
│   ├── rl_agent.py                  # RL-controlled unit
│   ├── config.py                     # Configuration presets
│   └── README.md                     # Документація модуля
│
├── train_rl.py                       # Головний скрипт тренування
├── quick_start_rl.py                 # Інтерактивний швидкий старт
├── test_rl_setup.py                  # Тест на коректність налаштувань
├── RL_GUIDE.md                       # Детальний гід по RL
└── RL_IMPLEMENTATION_SUMMARY.md      # Цей документ
```

### Змінені файли

```
requirements.txt                      # Додано RL залежності
```

## Компоненти системи

### 1. Observation Space (330 features)

**Власний стан (10 features):**
- Позиція (x, y)
- HP (normalized)
- Attack power, range, accuracy (normalized)
- Armor, speed (normalized)
- Direction (sin, cos)

**Вороги (20 × 8 = 160 features):**
- Відносна позиція (dx, dy)
- Дистанція
- HP ratio
- Unit type
- Attack stats
- In range flag

**Союзники (20 × 8 = 160 features):**
- Аналогічно ворогам

### 2. Action Space (13 дискретних дій)

**Рух (0-8):**
- 0: North, 1: South, 2: East, 3: West
- 4: NE, 5: NW, 6: SE, 7: SW
- 8: Stay

**Атака (9-11):**
- 9: Attack nearest enemy
- 10: Attack weakest (lowest HP)
- 11: Attack strongest (highest HP)

**Тактика (12):**
- 12: Retreat from nearest enemy

### 3. Reward Function

**Позитивні винагороди:**
- Kill enemy: +10.0
- Hit enemy: +1.0
- Survival per step: +0.1
- Enemy in range: +0.5
- Team kill bonus: +5.0 (shared)
- Win battle: +100.0

**Негативні штрафи:**
- Miss: -0.1
- Damage taken: -2.0 (per HP ratio)
- Death: -50.0
- Too far from enemies: -0.01
- Lose battle: -100.0

### 4. Алгоритм навчання

**PPO (Proximal Policy Optimization):**
- Learning rate: 3e-4
- Steps per rollout: 2048
- Batch size: 64
- Epochs per update: 10
- Gamma (discount): 0.99
- GAE lambda: 0.95
- Clip range: 0.2

## Як використовувати

### Крок 1: Встановлення

```bash
# Встановити залежності
pip install -r requirements.txt
```

### Крок 2: Перевірка налаштувань

```bash
# Запустити тест
python test_rl_setup.py
```

### Крок 3: Швидкий старт (інтерактивний)

```bash
# Інтерактивне меню
python quick_start_rl.py
```

Опції:
1. Демонстрація середовища
2. Просте тренування (10,000 кроків)
3. Порівняння випадковий vs навчений
4. Вихід

### Крок 4: Повне тренування

```bash
# Базове тренування
python train_rl.py --mode train --timesteps 100000

# Швидке тренування (для тестів)
python train_rl.py --mode train --timesteps 10000 --n-envs 2

# Довге тренування (для якості)
python train_rl.py --mode train --timesteps 1000000 --n-envs 8

# Тренування сторони B
python train_rl.py --mode train --side B --timesteps 100000
```

### Крок 5: Моніторинг

```bash
# Запустити TensorBoard
tensorboard --logdir models/
```

Відкрити браузер: `http://localhost:6006`

### Крок 6: Тестування

```bash
# Тест навченої моделі
python train_rl.py --mode test-model --model-path models/ppo_combat_YYYYMMDD_HHMMSS/final_model.zip
```

## Архітектура

### Single-Agent (поточна реалізація)

```
┌─────────────────────────────────────┐
│   CombatRLEnvironment               │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  ObservationBuilder          │  │
│  │  - Builds 330-dim vector     │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  ActionSpace                 │  │
│  │  - 13 discrete actions       │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  RewardCalculator            │  │
│  │  - Computes rewards          │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  CombatSimulation (Mesa)     │  │
│  │  - Controlled agent (RL)     │  │
│  │  - Opponent agents (script)  │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   PPO Agent (Stable-Baselines3)     │
│                                     │
│   Policy Network (MLP)              │
│   - Input: 330 features             │
│   - Hidden: [256, 256]              │
│   - Output: 13 action probabilities │
└─────────────────────────────────────┘
```

### Multi-Agent (майбутня розробка)

```
MultiAgentCombatEnvironment
├── Agent 1 (RL) ─┐
├── Agent 2 (RL) ─┼─► Shared Policy (Optional)
├── Agent 3 (RL) ─┘
└── Opponents (Scripted AI)
```

## Модифікації в існуючих модулях

### Модулі БЕЗ змін:

✓ `simulation/model.py` - використовується як є
✓ `simulation/units.py` - використовується як є
✓ `simulation/rules.py` - використовується як є
✓ `simulation/data_loader.py` - використовується як є
✓ `app.py` - Flask API залишається незмінним
✓ `config.py` - основна конфігурація залишається

### Додані модулі:

✓ `simulation/rl/*` - весь RL функціонал
✓ `train_rl.py` - тренувальний скрипт
✓ `quick_start_rl.py` - інтерактивний демо
✓ `test_rl_setup.py` - тестування налаштувань

## Приклади коду

### Базове тренування

```python
from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO

# Створити середовище
env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A',
    max_steps=1000
)

# Створити модель
model = PPO('MlpPolicy', env, verbose=1)

# Тренувати
model.learn(total_timesteps=100000)

# Зберегти
model.save('my_model')
```

### Тестування моделі

```python
from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO

# Завантажити модель
model = PPO.load('my_model')

# Створити середовище
env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A'
)

# Тестувати
obs, info = env.reset()
for _ in range(1000):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        print(f"Episode finished: reward={reward}, hp={info['hp']}")
        break
```

### Використання конфігурації

```python
from simulation.rl.config import get_config
from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO

# Завантажити конфігурацію
config = get_config('fast')  # 'default', 'fast', 'quality', 'multi_agent'

# Створити середовище з конфігом
env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side=config['env']['controlled_side'],
    max_steps=config['env']['max_steps']
)

# Створити модель з конфігом
model = PPO(
    'MlpPolicy',
    env,
    learning_rate=config['ppo']['learning_rate'],
    n_steps=config['ppo']['n_steps'],
    batch_size=config['ppo']['batch_size'],
    verbose=1
)

# Тренувати з конфігом
model.learn(total_timesteps=config['training']['total_timesteps'])
```

## Метрики для оцінки

### Під час тренування (TensorBoard):

- `rollout/ep_rew_mean` - середня винагорода за епізод
- `rollout/ep_len_mean` - середня довжина епізоду
- `train/learning_rate` - поточний learning rate
- `train/loss` - функція втрат
- `train/policy_gradient_loss` - втрати policy
- `train/value_loss` - втрати value function
- `train/entropy_loss` - ентропія (exploration)

### Після тренування:

- **Win Rate** - % перемог проти scripted AI
- **Average Reward** - середня винагорода за епізод
- **Kill/Death Ratio** - співвідношення вбивств до смертей
- **Average Survival Time** - середній час виживання
- **Hit Accuracy** - точність пострілів

## Наступні кроки

### Короткострокові:

1. ✓ Базова реалізація single-agent RL
2. ⏳ Налаштування reward function для кращої конвергенції
3. ⏳ Експерименти з hyperparameters
4. ⏳ Порівняння різних алгоритмів (A2C, DQN, SAC)

### Середньострокові:

5. ⏳ Multi-agent навчання (всі юніти сторони)
6. ⏳ Communication між агентами
7. ⏳ Curriculum learning (поступове ускладнення)
8. ⏳ Self-play (обидві сторони навчаються)

### Довгострокові:

9. ⏳ Hierarchical RL (командир + юніти)
10. ⏳ Opponent modeling
11. ⏳ Meta-learning для адаптації до різних сценаріїв
12. ⏳ Transfer learning між різними типами юнітів

## Налаштування продуктивності

### Для швидкого тренування:

```python
config = get_config('fast')
# - 10,000 timesteps
# - 2 parallel environments
# - Smaller network
```

### Для якісного тренування:

```python
config = get_config('quality')
# - 1,000,000 timesteps
# - 8 parallel environments
# - Larger network
# - More epochs
```

### Для дебагу:

```python
# Встановити verbose=2 для детального логування
model = PPO('MlpPolicy', env, verbose=2)
```

## Troubleshooting

### Проблема: ModuleNotFoundError

**Рішення:** Встановіть залежності
```bash
pip install -r requirements.txt
```

### Проблема: Модель не навчається

**Рішення:**
- Перевірте reward function в `simulation/rl/rewards.py`
- Зменшіть learning rate
- Збільште exploration (ent_coef)

### Проблема: Дуже повільно

**Рішення:**
- Збільште `n_envs` для паралелізації
- Використовуйте GPU (PyTorch з CUDA)
- Зменшіть `max_enemies` та `max_allies` в observation

### Проблема: Out of memory

**Рішення:**
- Зменшіть `n_envs`
- Зменшіть `batch_size`
- Зменшіть розмір observation space

## Додаткові ресурсі

### Документація:
- [RL_GUIDE.md](RL_GUIDE.md) - детальний гід
- [simulation/rl/README.md](simulation/rl/README.md) - документація модуля

### Скрипти:
- `test_rl_setup.py` - тестування
- `quick_start_rl.py` - швидкий старт
- `train_rl.py` - повне тренування

### Зовнішні ресурси:
- [Stable-Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Docs](https://gymnasium.farama.org/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)

## Автори

Розроблено як розширення Combat Simulation System для додавання можливостей навчання з підкріпленням.

---

**Готово до використання!** Почніть з `python test_rl_setup.py` для перевірки налаштувань.
