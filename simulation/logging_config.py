"""
Асинхронна система логування для Combat Simulation System
Використовує QueueHandler для мінімізації впливу на продуктивність
Всі логи пишуться на диск в окремих потоках
"""

import logging
import logging.handlers
import os
import json
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
import sys


class AsyncCombatLogger:
    """Асинхронний логер для бойових подій в JSON форматі"""

    def __init__(self, log_dir, session_id):
        self.log_dir = Path(log_dir)
        self.session_id = session_id
        self.file_path = self.log_dir / 'combat' / f'combat_{session_id}.json'

        print(f"Initializing AsyncCombatLogger for session: {session_id}")
        print(f"Combat log will be written to: {self.file_path.absolute()}")

        # Черга для асинхронного запису
        self.queue = Queue()
        self.running = True

        # Лічильники для статистики
        self.stats = {
            'total_events': 0,
            'shots': 0,
            'hits': 0,
            'destroyed': 0,
            'moves': 0
        }
        self.stats_lock = threading.Lock()

        # Запустити worker thread для запису на диск
        self.writer_thread = threading.Thread(target=self._writer_worker, daemon=True)
        self.writer_thread.start()

        # Створити symlink до latest
        self._create_latest_link()

    def _create_latest_link(self):
        """Створити symlink до останнього файлу"""
        latest_path = self.log_dir / 'combat' / 'combat_latest.json'
        if latest_path.exists() or latest_path.is_symlink():
            try:
                latest_path.unlink()
            except:
                pass

        try:
            # Windows потребує або admin права, або developer mode для symlinks
            # Тому просто створимо текстовий файл з посиланням
            with open(latest_path, 'w') as f:
                f.write(str(self.file_path.absolute()))
        except Exception as e:
            pass  # Не критично якщо не вдалось

    def _writer_worker(self):
        """Worker thread що записує події на диск"""
        try:
            # Переконатися що директорія існує
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"Combat logger writing to: {self.file_path}")

            with open(self.file_path, 'w', encoding='utf-8') as f:
                events_written = 0
                while self.running or not self.queue.empty():
                    try:
                        # Отримати подію з черги (timeout щоб перевіряти running)
                        event = self.queue.get(timeout=0.1)

                        # Записати на диск
                        f.write(json.dumps(event, ensure_ascii=False) + '\n')
                        f.flush()  # Гарантувати запис
                        events_written += 1

                        self.queue.task_done()

                    except:
                        # Timeout - черга порожня
                        continue

                print(f"Combat logger finished: {events_written} events written to {self.file_path}")

        except Exception as e:
            print(f"ERROR in combat logger writer thread: {e}")
            import traceback
            traceback.print_exc()

    def log_event(self, event_type, step, attacker, target, **kwargs):
        """
        Додати подію в чергу для асинхронного запису

        Args:
            event_type: Тип події ('shot', 'hit', 'destroyed', 'move')
            step: Номер кроку симуляції
            attacker: Об'єкт юніта-атакуючого
            target: Об'єкт юніта-цілі
            **kwargs: Додаткові дані події
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'event_type': event_type,
            'attacker': {
                'id': attacker.unit_id,
                'name': attacker.name,
                'type': attacker.unit_type,
                'side': attacker.side,
                'position': list(attacker.pos)
            },
            'target': {
                'id': target.unit_id,
                'name': target.name,
                'type': target.unit_type,
                'side': target.side,
                'position': list(target.pos),
                'hp': round(target.hp, 2),
                'max_hp': target.max_hp
            }
        }

        # Додати додаткові дані
        event.update(kwargs)

        # Додати в чергу (не блокує симуляцію)
        self.queue.put(event)

        # Оновити статистику
        with self.stats_lock:
            self.stats['total_events'] += 1
            if event_type in self.stats:
                self.stats[event_type] += 1

            # Діагностика кожні 100 подій
            if self.stats['total_events'] % 100 == 0:
                print(f"Combat logger: {self.stats['total_events']} events queued (queue size: {self.queue.qsize()})")

    def get_stats(self):
        """Отримати статистику подій"""
        with self.stats_lock:
            return self.stats.copy()

    def shutdown(self):
        """Зупинити асинхронний запис та дочекатись завершення"""
        if not self.running:
            return  # Вже зупинено

        self.running = False

        # Дочекатись поки черга спорожніє (з timeout)
        try:
            self.queue.join()
        except Exception:
            pass

        # Дочекатись завершення worker thread
        if self.writer_thread.is_alive():
            self.writer_thread.join(timeout=5.0)

        # Якщо thread все ще живий, це проблема, але не критична
        if self.writer_thread.is_alive():
            print(f"Warning: Combat logger thread did not stop cleanly")

        # Записати статистику
        try:
            self._write_summary()
        except Exception as e:
            print(f"Warning: Could not write combat log summary: {e}")

    def _write_summary(self):
        """Записати summary файл з статистикою"""
        summary_path = self.file_path.with_name(f'combat_{self.session_id}_summary.json')

        with self.stats_lock:
            summary = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'statistics': self.stats.copy()
            }

        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not write summary: {e}")


class ColoredFormatter(logging.Formatter):
    """Форматер з кольоровим виводом для консолі (опціонально)"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record):
        # Колір тільки якщо вивід в термінал
        if sys.stdout.isatty() and os.name != 'nt':  # Unix/Linux
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


class PerformanceTimer:
    """Context manager для вимірювання часу виконання"""

    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.perf_counter() - self.start_time
        self.logger.debug(f"{self.operation_name} took {duration*1000:.2f}ms")
        return False


class SimulationLogger:
    """
    Централізована фабрика логерів для симуляції
    Використовує QueueHandler для асинхронного запису
    """

    _loggers = {}
    _initialized = False
    _log_dir = None
    _current_session = None
    _queue_listener = None
    _combat_logger = None

    @classmethod
    def initialize(cls, log_dir='logs', log_level=logging.INFO, session_id=None,
                   enable_console=False, enable_combat_log=True):
        """
        Ініціалізувати систему логування

        Args:
            log_dir: Директорія для лог-файлів
            log_level: Мінімальний рівень логування
            session_id: Унікальний ідентифікатор сесії
            enable_console: Виводити в консоль (може сповільнити)
            enable_combat_log: Вести JSON лог бойових подій
        """
        if cls._initialized:
            return

        cls._log_dir = Path(log_dir)
        cls._log_dir.mkdir(parents=True, exist_ok=True)

        # Створити піддиректорії
        (cls._log_dir / 'simulation').mkdir(exist_ok=True)
        (cls._log_dir / 'combat').mkdir(exist_ok=True)
        (cls._log_dir / 'errors').mkdir(exist_ok=True)
        (cls._log_dir / 'performance').mkdir(exist_ok=True)

        # Генерувати session ID
        cls._current_session = session_id or datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Ініціалізувати combat logger
        if enable_combat_log:
            cls._combat_logger = AsyncCombatLogger(cls._log_dir, cls._current_session)

        cls._initialized = True
        cls._enable_console = enable_console

        # НЕ використовуємо atexit.register - це викликає конфлікти з Flask
        # Замість цього shutdown викликається вручну або через signal handlers

        # Логувати ініціалізацію
        logger = cls.get_logger('system')
        logger.info("="*60)
        logger.info(f"Logging system initialized - Session: {cls._current_session}")
        logger.info(f"Log directory: {cls._log_dir.absolute()}")
        logger.info(f"Log level: {logging.getLevelName(log_level)}")
        logger.info(f"Console output: {enable_console}")
        logger.info(f"Combat logging: {enable_combat_log}")
        logger.info("="*60)

    @classmethod
    def get_logger(cls, name, log_level=None):
        """
        Отримати або створити логер з вказаним ім'ям

        Args:
            name: Ім'я логера (e.g., 'model', 'units', 'combat')
            log_level: Перевизначити рівень логування

        Returns:
            Налаштований logger instance
        """
        if not cls._initialized:
            cls.initialize()

        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(f'combat_sim.{name}')
        logger.setLevel(log_level or logging.DEBUG)
        logger.propagate = False

        # Створити handlers для listener
        handlers = []

        # Console handler (опціонально)
        if cls._enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            handlers.append(console_handler)

        # File handler - Загальний лог
        file_path = cls._log_dir / 'simulation' / f'simulation_{cls._current_session}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

        # Error handler - Окремий файл для помилок
        error_path = cls._log_dir / 'errors' / f'errors_{datetime.now().strftime("%Y-%m-%d")}.log'
        error_handler = logging.FileHandler(error_path, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        handlers.append(error_handler)

        # Створити чергу для асинхронного запису
        log_queue = Queue(-1)  # Необмежена черга

        # QueueHandler - дуже швидкий, просто додає в чергу
        queue_handler = logging.handlers.QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        # QueueListener - записує на диск в окремому потоці
        if cls._queue_listener is None:
            cls._queue_listener = logging.handlers.QueueListener(
                log_queue,
                *handlers,
                respect_handler_level=True
            )
            cls._queue_listener.start()

        # Створити symlink до latest (для зручності)
        cls._create_latest_symlink(file_path)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def _create_latest_symlink(cls, file_path):
        """Створити посилання на останній лог-файл"""
        latest_path = cls._log_dir / 'simulation' / 'simulation_latest.log'
        if latest_path.exists() or latest_path.is_symlink():
            try:
                latest_path.unlink()
            except:
                pass

        try:
            # На Windows можуть бути проблеми з symlinks, створюємо текстовий файл
            with open(latest_path, 'w') as f:
                f.write(str(file_path.absolute()))
        except Exception:
            pass  # Не критично

    @classmethod
    def get_combat_logger(cls):
        """Отримати спеціалізований логер бойових подій (JSON формат)"""
        if not cls._initialized:
            cls.initialize()

        return cls._combat_logger

    @classmethod
    def get_performance_logger(cls):
        """Отримати логер метрик продуктивності"""
        return cls.get_logger('performance')

    @classmethod
    def reset(cls):
        """Скинути систему логування для нової симуляції"""
        if cls._initialized:
            cls.shutdown()
        # Тепер можна ініціалізувати заново з новим session_id

    @classmethod
    def shutdown(cls):
        """Очистити та закрити всі логери"""
        if not cls._initialized:
            return

        print("Shutting down logging system...")

        # Зупинити combat logger спочатку (він має власний thread)
        if cls._combat_logger is not None:
            try:
                cls._combat_logger.shutdown()
            except Exception as e:
                print(f"Warning: Error shutting down combat logger: {e}")
            finally:
                cls._combat_logger = None

        # Зупинити queue listener
        if cls._queue_listener is not None:
            try:
                cls._queue_listener.stop()
            except Exception as e:
                print(f"Warning: Error stopping queue listener: {e}")
            finally:
                cls._queue_listener = None

        # Закрити всі handlers
        for logger in cls._loggers.values():
            if isinstance(logger, logging.Logger):
                try:
                    for handler in logger.handlers[:]:
                        try:
                            handler.flush()
                            handler.close()
                        except Exception:
                            pass
                        try:
                            logger.removeHandler(handler)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Warning: Error closing logger handlers: {e}")

        cls._loggers.clear()
        cls._initialized = False

        print("Logging system shut down successfully")


# Convenience functions
def get_logger(name):
    """Зручна функція для отримання логера"""
    return SimulationLogger.get_logger(name)


def get_combat_logger():
    """Зручна функція для отримання combat логера"""
    return SimulationLogger.get_combat_logger()


def get_performance_timer(logger, operation_name):
    """Зручна функція для створення performance timer"""
    return PerformanceTimer(logger, operation_name)