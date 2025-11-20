# 🚀 RL Quick Start

## Швидкий старт за 3 кроки

### 📦 Крок 1: Встановлення (2 хв)

```bash
pip install -r requirements.txt
```

### ✅ Крок 2: Перевірка (1 хв)

```bash
python test_rl_setup.py
```

Якщо всі тести пройшли - готово! ✓

### 🎮 Крок 3: Запуск (2 хв)

```bash
python quick_start_rl.py
```

Оберіть опцію `2` для швидкого тренування.

---

## Що далі?

### Для швидкого експерименту:

```bash
python train_rl.py --mode train --timesteps 10000 --n-envs 2
```

### Для якісного тренування:

```bash
python train_rl.py --mode train --timesteps 100000 --n-envs 4
```

### Для моніторингу:

```bash
tensorboard --logdir models/
```

Відкрийте: http://localhost:6006

---

## 📚 Документація

- **[RL_GUIDE.md](RL_GUIDE.md)** - детальний гід
- **[RL_IMPLEMENTATION_SUMMARY.md](RL_IMPLEMENTATION_SUMMARY.md)** - технічний опис
- **[simulation/rl/README.md](simulation/rl/README.md)** - документація модуля

---

## 🎯 Що робить RL?

```
Scripted AI (було):                  RL Agent (стало):
┌─────────────────────┐              ┌─────────────────────┐
│ IF enemy nearby:    │              │ Neural Network:     │
│   attack nearest    │              │ - Learns strategy   │
│ ELSE:               │              │ - Adapts to enemy   │
│   move forward      │              │ - Optimizes tactics │
└─────────────────────┘              └─────────────────────┘
```

**RL агент навчається:**
- Коли атакувати
- Коли відступати
- Як вибирати цілі
- Як позиціонуватися
- Як координуватися з командою

---

## 🔧 Структура

```
Combat Simulation RL
├── 🧠 Навчання
│   ├── train_rl.py           (головний скрипт)
│   ├── quick_start_rl.py     (інтерактивний демо)
│   └── test_rl_setup.py      (тестування)
│
├── 🎮 RL Модулі
│   ├── environment.py        (Gym середовище)
│   ├── observation.py        (що бачить агент)
│   ├── actions.py            (що може робити)
│   ├── rewards.py            (що отримує за дії)
│   └── config.py             (налаштування)
│
└── 📖 Документація
    ├── RL_GUIDE.md           (повний гід)
    ├── RL_IMPLEMENTATION_SUMMARY.md
    └── RL_QUICKSTART.md      (цей файл)
```

---

## 💡 Приклади використання

### Базове тренування

```python
from simulation.rl import CombatRLEnvironment
from stable_baselines3 import PPO

env = CombatRLEnvironment(
    objects_file='data/objects.xlsx',
    rules_file='data/sets.xlsx',
    controlled_side='A'
)

model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=100000)
model.save('my_model')
```

### Тестування моделі

```python
model = PPO.load('my_model')
env = CombatRLEnvironment(...)

obs, info = env.reset()
for _ in range(1000):
    action, _ = model.predict(obs)
    obs, reward, done, truncated, info = env.step(action)
    if done or truncated:
        break
```

---

## ⚙️ Налаштування

### Швидкість vs Якість

| Параметр | Швидко | Збалансовано | Якісно |
|----------|--------|--------------|--------|
| timesteps | 10,000 | 100,000 | 1,000,000 |
| n_envs | 2 | 4 | 8 |
| Час | 5 хв | 30 хв | 5 год |

### Команди

```bash
# Швидко (тестування)
python train_rl.py --mode train --timesteps 10000 --n-envs 2

# Збалансовано
python train_rl.py --mode train --timesteps 100000 --n-envs 4

# Якісно
python train_rl.py --mode train --timesteps 1000000 --n-envs 8
```

---

## 🐛 Troubleshooting

### Помилка: ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Помилка: File not found (objects.xlsx)

Перевірте наявність файлів:
- `data/objects.xlsx`
- `data/sets.xlsx`

### Модель не навчається

1. Збільште `timesteps`
2. Налаштуйте rewards в `simulation/rl/rewards.py`
3. Запустіть TensorBoard для моніторингу

---

## 📊 Метрики успіху

Після тренування оцініть модель за:

- ✓ **Win Rate** > 50% проти scripted AI
- ✓ **Average Reward** > 0
- ✓ **Survival Time** збільшується з тренуванням
- ✓ **Kill/Death Ratio** > 1.0

---

## 🎓 Додаткові ресурси

### Внутрішні:
- `RL_GUIDE.md` - повний гід
- `quick_start_rl.py` - інтерактивні приклади
- `simulation/rl/README.md` - API документація

### Зовнішні:
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- [Gymnasium](https://gymnasium.farama.org/)
- [RL Tutorial](https://spinningup.openai.com/)

---

## ✨ Що нового?

### До (Scripted AI):
```python
def step(self):
    target = self.find_nearest_enemy()
    if target:
        self.attack(target)
    else:
        self.move_forward()
```

### Після (RL):
```python
def step(self):
    observation = self.build_observation()
    action = self.policy(observation)  # Neural network
    self.execute(action)
```

**Різниця:** RL агент навчається оптимальній стратегії через тисячі симуляцій!

---

## 🚀 Готові почати?

```bash
# 1. Встановити
pip install -r requirements.txt

# 2. Перевірити
python test_rl_setup.py

# 3. Запустити демо
python quick_start_rl.py

# 4. Тренувати
python train_rl.py --mode train

# 5. Спостерігати
tensorboard --logdir models/
```

**Успіхів у навчанні! 🎉**
