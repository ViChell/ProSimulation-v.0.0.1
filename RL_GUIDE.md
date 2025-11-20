# Reinforcement Learning Training Guide

Цей гід пояснює, як тренувати агентів за допомогою навчання з підкріпленням (RL).

## Встановлення

```bash
# Встановіть RL залежності
pip install -r requirements.txt
```

## Швидкий старт

### 1. Тест середовища (без тренування)

Перевірте, що RL середовище працює коректно:

```bash
python train_rl.py --mode test
```

Це запустить агента з випадковими діями протягом кількох кроків для перевірки середовища.

### 2. Базове тренування

Почніть тренування з параметрами за замовчуванням:

```bash
python train_rl.py --mode train --timesteps 100000
```

Параметри:
- `--timesteps`: Кількість кроків тренування (default: 100000)
- `--n-envs`: Кількість паралельних середовищ (default: 4)
- `--side`: Яку сторону тренувати - 'A' або 'B' (default: 'A')
- `--save-dir`: Директорія для збереження моделей (default: 'models')

### 3. Спостереження за тренуванням

Під час тренування ви можете відстежувати прогрес за допомогою TensorBoard:

```bash
tensorboard --logdir models/
```

Відкрийте браузер на `http://localhost:6006`

### 4. Тестування натренованої моделі

Після завершення тренування протестуйте модель:

```bash
python train_rl.py --mode test-model --model-path models/ppo_combat_YYYYMMDD_HHMMSS/final_model.zip
```

## Архітектура RL системи

### Компоненти

```
simulation/rl/
├── environment.py      # Gym environment wrapper
├── observation.py      # Observation space builder
├── actions.py          # Action space handler
├── rewards.py          # Reward calculation
└── rl_agent.py        # RL-controlled unit class
```

### Observation Space

Кожна observation містить:

**Власний стан (10 features):**
- Позиція (x, y)
- Нормалізоване HP
- Сила атаки, дальність, точність
- Броня, швидкість
- Напрямок (sin, cos)

**Вороги (до 20 × 8 features):**
- Відносна позиція
- Дистанція
- HP
- Тип юніта
- Характеристики
- Чи в радіусі атаки

**Союзники (до 20 × 8 features):**
- Аналогічно ворогам

**Загальний розмір:** 10 + 20×8 + 20×8 = 330 features

### Action Space

13 дискретних дій:

**Рух (0-8):**
- 0-7: Рух у 8 напрямках (N, S, E, W, NE, NW, SE, SW)
- 8: Залишитись на місці

**Атака (9-11):**
- 9: Атакувати найближчого
- 10: Атакувати найслабшого (lowest HP)
- 11: Атакувати найсильнішого (highest HP)

**Тактика (12):**
- 12: Відступити від ворога

### Reward Function

Винагороди:

**Позитивні:**
- +10.0: Знищення ворога
- +1.0: Влучення по ворогу
- +0.1: Виживання (за крок)
- +0.5: Наявність ворога в радіусі атаки
- +5.0: Знищення ворога союзником (кооперація)
- +100.0: Перемога в бою

**Негативні:**
- -0.1: Промах
- -2.0: Отримання пошкоджень (за HP)
- -50.0: Смерть агента
- -0.01: Відстань від ворога (якщо занадто далеко)
- -100.0: Програш бою

## Налаштування параметрів

### Hyperparameters (у train_rl.py)

```python
learning_rate=3e-4      # Швидкість навчання
n_steps=2048            # Кроків на rollout
batch_size=64           # Розмір minibatch
n_epochs=10             # Епох на update
gamma=0.99              # Discount factor
gae_lambda=0.95         # GAE lambda
clip_range=0.2          # PPO clip range
ent_coef=0.01           # Entropy coefficient
```

### Reward Weights (у simulation/rl/rewards.py)

Відредагуйте `RewardCalculator.__init__()` для зміни балансу винагород:

```python
self.config = {
    'kill_reward': 10.0,
    'hit_reward': 1.0,
    # ... інші параметри
}
```

## Приклади використання

### Швидке тренування (для тестування)

```bash
python train_rl.py --mode train --timesteps 10000 --n-envs 2
```

### Довге тренування (для якості)

```bash
python train_rl.py --mode train --timesteps 1000000 --n-envs 8
```

### Тренування сторони B

```bash
python train_rl.py --mode train --side B --timesteps 100000
```

### Порівняння RL vs Scripted AI

1. Тренуйте агента сторони A:
```bash
python train_rl.py --mode train --side A --timesteps 500000
```

2. Тестуйте проти scripted AI (сторона B):
```bash
python train_rl.py --mode test-model --model-path models/.../final_model.zip
```

## Розширені можливості

### Multi-Agent Training

Для тренування всіх юнітів однієї сторони одночасно, використовуйте `MultiAgentCombatEnvironment` у `environment.py`.

### Custom Policy Network

Змініть архітектуру нейронної мережі в `train_rl.py`:

```python
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class CustomNetwork(BaseFeaturesExtractor):
    # ... ваша архітектура
```

### Curriculum Learning

Поступово ускладнюйте сценарії:
1. 1v1 combat
2. 3v3 combat
3. 5v5 combat
4. Повний бій

## Troubleshooting

### Проблема: Модель не навчається

**Рішення:**
- Зменшіть learning rate
- Збільште entropy coefficient
- Перевірте reward function
- Візуалізуйте в TensorBoard

### Проблема: Модель надто консервативна

**Рішення:**
- Збільште ent_coef (наприклад, до 0.05)
- Зменшіть penalty за смерть
- Збільште reward за знищення

### Проблема: Модель занадто агресивна

**Рішення:**
- Збільште penalty за смерть
- Додайте reward за виживання
- Зменшіть kill_reward

## Метрики для оцінки

Відстежуйте в TensorBoard:

- **Episode Reward**: Загальна винагорода за епізод
- **Episode Length**: Тривалість епізоду
- **Win Rate**: Частка перемог
- **Mean HP**: Середнє HP після епізоду
- **Kill/Death Ratio**: Співвідношення вбивств до смертей

## Наступні кроки

1. **Тонке налаштування**: Експериментуйте з reward weights
2. **Архітектура**: Спробуйте різні neural network architectures
3. **Multi-Agent**: Тренуйте команду агентів
4. **Hierarchical RL**: Додайте командира
5. **Self-Play**: Тренуйте обидві сторони одна проти одної

## Додаткові ресурси

- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)
- [Multi-Agent RL](https://arxiv.org/abs/1911.10635)
