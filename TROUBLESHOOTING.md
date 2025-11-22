# Troubleshooting Guide

## ✅ Виправлені проблеми

### OSError: [WinError 10038] An operation was attempted on something that is not a socket

**Симптоми:**
```
Exception in thread Thread-4 (serve_forever):
OSError: [WinError 10038] An operation was attempted on something that is not a socket
Logging system shut down successfully
```

**Причина:**
Конфлікт між `atexit.register()` в системі логування та Flask lifecycle. Коли Flask завершувався, `atexit` спрацьовував занадто рано і закривав логери, поки Flask threads ще працювали.

**Рішення:**
1. Видалено `atexit.register()` з `logging_config.py`
2. Додано правильний shutdown handler в `app.py`:
   - Signal handlers (SIGINT, SIGTERM)
   - Try-finally блок навколо `app.run()`
   - Явний виклик `SimulationLogger.shutdown()`
3. Покращено error handling в методі `shutdown()`
4. Вимкнено Flask reloader (`use_reloader=False`)

**Статус:** ✅ Виправлено

---

## 🔧 Загальні проблеми

### Проблема: Логи не створюються

**Перевірте:**
1. `config.py`: `LOGGING_ENABLED = True`
2. Права на запис в директорію `logs/`
3. Консоль на помилки ініціалізації

### Проблема: Симуляція працює повільно

**Рішення:**
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

**Автоматична ротація:**
- Simulation log: максимум 10MB, 5 backup файлів (50MB всього)
- Combat JSON: необмежений (видаляйте старі вручну)
- Error log: один файл на день

**Ручне очищення:**
```bash
# Видалити всі логи старші 7 днів
find logs/ -type f -mtime +7 -delete

# Або на Windows PowerShell
Get-ChildItem -Path logs -Recurse -File | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

### Проблема: Flask reloader запускає симуляцію двічі

**Рішення:**
В `app.py` використовується `use_reloader=False`:
```python
app.run(
    host=config.FLASK_HOST,
    port=config.FLASK_PORT,
    debug=config.DEBUG,
    use_reloader=False  # Важливо!
)
```

Якщо потрібен reloader для розробки, створіть окремий dev режим.

### Проблема: Thread warnings при завершенні

**Якщо бачите:**
```
Warning: Combat logger thread did not stop cleanly
```

Це означає що combat logger не встиг записати всі події за 5 секунд timeout.

**Рішення:**
- Зачекайте декілька секунд перед повторним запуском
- Або збільшіть timeout в `logging_config.py`:
```python
self.writer_thread.join(timeout=10.0)  # 10 секунд замість 5
```

---

## 📝 Debugging Tips

### Включити детальне логування

```python
# config.py
LOG_LEVEL = 'DEBUG'
ENABLE_CONSOLE_OUTPUT = True  # Тільки для debugging!
```

### Перевірити чи працює асинхронне логування

Додайте в код:
```python
from simulation.logging_config import SimulationLogger

logger = SimulationLogger.get_logger('test')
logger.info("Test message")

# Перевірити статус
print(f"Initialized: {SimulationLogger._initialized}")
print(f"Loggers: {list(SimulationLogger._loggers.keys())}")
```

### Моніторинг черг логування

Для діагностики можна додати:
```python
# В logging_config.py, метод _writer_worker
def _writer_worker(self):
    while self.running or not self.queue.empty():
        print(f"Queue size: {self.queue.qsize()}")  # Діагностика
        # ... існуючий код
```

---

## 🆘 Якщо нічого не допомагає

1. Повністю видаліть директорію `logs/`
2. Перезапустіть Python процес
3. Запустіть з мінімальною конфігурацією:
   ```python
   LOGGING_ENABLED = False
   ```
4. Поступово вмикайте функції логування

---

## 📞 Контакт

Для додаткової допомоги створіть issue з:
- Версією Python
- Версією Flask
- Повним traceback помилки
- Конфігурацією з `config.py`
