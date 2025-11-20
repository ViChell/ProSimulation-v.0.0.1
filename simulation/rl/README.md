# Reinforcement Learning Module

Цей модуль додає можливість навчання агентів за допомогою Reinforcement Learning до Combat Simulation System.

## Структура модуля

```
simulation/rl/
├── __init__.py         # Експорти модуля
├── environment.py      # Gymnasium environment wrapper
├── observation.py      # Observation space builder
├── actions.py          # Action space definition
├── rewards.py          # Reward calculator
├── rl_agent.py        # RL-controlled unit class
├── config.py          # Configuration presets
└── README.md          # Ця документація
```

## Компоненти

### 1. Environment (`environment.py`)

**CombatRLEnvironment** - основне середовище для тренування одного агента.

```python
from simulation.rl import CombatRLEnvironment

env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A',
    max_steps=1000
)
```

**MultiAgentCombatEnvironment** - середовище для тренування всіх агентів сторони.

### 2. Observation Space (`observation.py`)

**ObservationBuilder** - будує вектор спостережень для агента.

Observation містить:
- Власний стан (10 features)
- Стани ворогів (до 20 × 8 features)
- Стани союзників (до 20 × 8 features)

Загальний розмір: 330 features

### 3. Action Space (`actions.py`)

**ActionSpace** - визначає та виконує дії агента.

13 дискретних дій:
- 0-7: Рух у 8 напрямках
- 8: Залишитись на місці
- 9-11: Атака (найближчий/слабкий/сильний)
- 12: Відступ

### 4. Rewards (`rewards.py`)

**RewardCalculator** - розраховує винагороди за дії.

Винагороди налаштовуються в конфігурації:
- Kill reward: +10.0
- Hit reward: +1.0
- Death penalty: -50.0
- Win reward: +100.0
- та інші...

### 5. RL Agent (`rl_agent.py`)

**RLMilitaryUnit** - юніт, керований RL policy.

```python
from simulation.rl import RLMilitaryUnit

unit = RLMilitaryUnit(
    model=model,
    unit_id=1,
    name="RL Tank",
    policy=trained_policy,
    # ... інші параметри
)
```

### 6. Configuration (`config.py`)

Конфігураційні пресети:
- `default`: Стандартне тренування
- `fast`: Швидке тренування для тестів
- `quality`: Високоякісне тренування
- `multi_agent`: Мультиагентне тренування

```python
from simulation.rl.config import get_config

config = get_config('fast')
```

## Швидкий старт

### Встановлення

```bash
pip install gymnasium stable-baselines3 torch tensorboard
```

### Простий приклад

```python
from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO

# Створити середовище
env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A'
)

# Створити модель
model = PPO('MlpPolicy', env, verbose=1)

# Тренувати
model.learn(total_timesteps=10000)

# Зберегти
model.save('my_model')

# Тестувати
obs, info = env.reset()
for _ in range(100):
    action, _ = model.predict(obs)
    obs, reward, done, truncated, info = env.step(action)
    if done or truncated:
        break
```

## Розширення

### Custom Observation Space

Створіть власний ObservationBuilder:

```python
class CustomObservationBuilder(ObservationBuilder):
    def build_observation(self, agent, model):
        # Ваша логіка
        return custom_observation
```

### Custom Reward Function

Створіть власний RewardCalculator:

```python
class CustomRewardCalculator(RewardCalculator):
    def calculate_reward(self, agent, model, action_result):
        # Ваша логіка винагород
        return reward
```

### Custom Action Space

Розширте ActionSpace:

```python
class ExtendedActionSpace(ActionSpace):
    # Додайте нові дії
    ACTION_FLANK = 13
    ACTION_COVER = 14
```

## Алгоритми

### Підтримувані алгоритми (через Stable-Baselines3)

- **PPO** (Proximal Policy Optimization) - рекомендований
- **A2C** (Advantage Actor-Critic)
- **DQN** (Deep Q-Network)
- **SAC** (Soft Actor-Critic)

### Приклад з A2C

```python
from stable_baselines3 import A2C

model = A2C('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=100000)
```

## Multi-Agent Training

Для тренування всіх юнітів однієї сторони:

```python
from simulation.rl.environment import MultiAgentCombatEnvironment

env = MultiAgentCombatEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A'
)

# Потребує multi-agent RL library (Ray RLlib, etc.)
```

## Метрики та логування

### TensorBoard

```bash
# Запустити під час тренування
tensorboard --logdir models/
```

### Власні метрики

```python
# У train_rl.py додайте callback
from stable_baselines3.common.callbacks import BaseCallback

class CustomCallback(BaseCallback):
    def _on_step(self):
        # Логуйте власні метрики
        self.logger.record('custom/my_metric', value)
        return True
```

## Performance Tips

1. **Використовуйте vectorized environments** (`n_envs > 1`)
2. **Налаштуйте reward shaping** для швидшого навчання
3. **Використовуйте curriculum learning** для складних сценаріїв
4. **Experiment з hyperparameters** через `config.py`

## Troubleshooting

### Модель не навчається
- Перевірте reward function
- Зменшіть learning rate
- Збільште exploration (ent_coef)

### Дуже повільно
- Збільште n_envs
- Зменшіть n_steps
- Використовуйте GPU для PyTorch

### Out of memory
- Зменшіть n_envs
- Зменшіть batch_size
- Зменшіть max_enemies/max_allies в observation

## Приклади використання

Дивіться:
- `../../train_rl.py` - Повне тренування
- `../../quick_start_rl.py` - Швидкий старт
- `../../RL_GUIDE.md` - Детальний гід

## Подальший розвиток

- [ ] Hierarchical RL (командир + юніти)
- [ ] Communication between agents
- [ ] Opponent modeling
- [ ] Self-play training
- [ ] Transfer learning
- [ ] Meta-learning

## Ліцензія

Частина Combat Simulation System project.
