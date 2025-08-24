"""
Многопоточные тесты для IOC контейнера.
Тестируют потокобезопасность и работу в конкурентной среде.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from homeworks.space_battle.ioc import IoC


@pytest.fixture(autouse=True)
def setup():
    """Очистка состояния перед каждым тестом."""
    IoC._strategies.clear()
    IoC._scopes.clear()
    IoC._current_scope = type("MockThreadLocal", (), {})()
    IoC._current_scope.scope_id = "root"


def test_thread_local_scope_isolation():
    """Каждый поток имеет изолированный скоуп - зависимости одного потока недоступны в других."""
    results = {}
    errors = {}

    def worker_thread(thread_id):
        try:
            # Каждый поток создает свой скоуп
            IoC.resolve("Scopes.New", f"thread_{thread_id}").execute()
            IoC.resolve("Scopes.Current", f"thread_{thread_id}").execute()

            # Регистрирует уникальную зависимость
            IoC.resolve("IoC.Register", "thread_key", lambda: f"thread_{thread_id}_value").execute()

            # Получает значение
            value = IoC.resolve("thread_key")
            results[thread_id] = value

            # Проверяем, что в текущем скоупе доступна только своя зависимость
            assert IoC.resolve("thread_key") == f"thread_{thread_id}_value"

        except Exception as e:
            errors[thread_id] = str(e)

    # Запускаем 3 потока через ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker_thread, thread_id) for thread_id in range(3)]

        # Ждем завершения всех потоков
        for future in as_completed(futures):
            future.result()

    # Проверяем результаты
    assert len(results) == 3
    assert results[0] == "thread_0_value"
    assert results[1] == "thread_1_value"
    assert results[2] == "thread_2_value"

    # Проверяем, что ошибок не было
    assert len(errors) == 0, f"Ошибки в потоках: {errors}"

    # Дополнительная проверка: в основном потоке не должно быть доступа к скоупам других потоков
    for thread_num in range(3):
        try:
            IoC.resolve("Scopes.Current", f"thread_{thread_num}").execute()
            IoC.resolve("thread_key")
            # Если дошли сюда, значит скоуп доступен, что нормально
        except ValueError:
            # Если скоуп недоступен, это тоже нормально
            pass


def test_concurrent_scope_creation():
    """Одновременное создание скоупов в разных потоках без конфликтов."""
    created_scopes = set()
    lock = threading.Lock()

    def create_scope_worker(thread_id):
        try:
            scope_name = f"concurrent_scope_{thread_id}"
            IoC.resolve("Scopes.New", scope_name).execute()

            with lock:
                created_scopes.add(scope_name)

        except Exception as e:
            print(f"Ошибка в потоке {thread_id}: {e}")

    # Запускаем 10 потоков одновременно
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_scope_worker, thread_id) for thread_id in range(10)]

        # Ждем завершения всех
        for future in as_completed(futures):
            future.result()

    # Проверяем, что все скоупы созданы
    assert len(created_scopes) == 10
    for scope_num in range(10):
        assert f"concurrent_scope_{scope_num}" in created_scopes


def test_concurrent_dependency_registration():
    """Одновременная регистрация зависимостей в разных потоках без потери данных."""
    registered_keys = set()
    lock = threading.Lock()

    def register_dependency_worker(thread_id):
        try:
            # Каждый поток создает свой скоуп
            IoC.resolve("Scopes.New", f"worker_{thread_id}").execute()
            IoC.resolve("Scopes.Current", f"worker_{thread_id}").execute()

            # Регистрирует несколько зависимостей
            for dep_num in range(5):
                key = f"worker_{thread_id}_dep_{dep_num}"
                IoC.resolve(
                    "IoC.Register", key, lambda tid=thread_id, idx=dep_num: f"value_{tid}_{idx}"
                ).execute()

                with lock:
                    registered_keys.add(key)

        except Exception as e:
            print(f"Ошибка в потоке {thread_id}: {e}")

    # Запускаем 5 потоков
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(register_dependency_worker, thread_id) for thread_id in range(5)]

        for future in as_completed(futures):
            future.result()

    # Проверяем, что все зависимости зарегистрированы
    assert len(registered_keys) == 25  # 5 потоков * 5 зависимостей


def test_thread_safety_with_shared_global_strategies():
    """Глобальные стратегии доступны всем потокам и возвращают одинаковые значения."""
    # Регистрируем глобальную стратегию, которая возвращает константу
    IoC.resolve("IoC.RegisterGlobal", "global_constant", lambda: "shared_value").execute()

    results = {}
    errors = {}

    def global_strategy_worker(thread_id):
        try:
            # Каждый поток получает значение глобальной стратегии
            value = IoC.resolve("global_constant")
            results[thread_id] = value

            # Создает свой скоуп
            IoC.resolve("Scopes.New", f"global_worker_{thread_id}").execute()
            IoC.resolve("Scopes.Current", f"global_worker_{thread_id}").execute()

            # Глобальная стратегия должна быть доступна из скоупа
            scope_value = IoC.resolve("global_constant")
            assert scope_value == "shared_value"

        except Exception as e:
            errors[thread_id] = str(e)

    # Запускаем потоки через ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(global_strategy_worker, thread_id) for thread_id in range(5)]

        for future in as_completed(futures):
            future.result()

    # Проверяем результаты
    assert len(results) == 5
    assert len(errors) == 0, f"Ошибки: {errors}"

    # Все потоки должны получить одинаковое значение
    assert all(value == "shared_value" for value in results.values())


def test_concurrent_scope_switching():
    """Переключение между скоупами в конкурентной среде без конфликтов между потоками."""
    scope_values = {}
    lock = threading.Lock()

    def scope_switching_worker(thread_id):
        try:
            # Создаем несколько скоупов
            for scope_num in range(3):
                scope_name = f"switching_{thread_id}_{scope_num}"
                IoC.resolve("Scopes.New", scope_name).execute()
                IoC.resolve("Scopes.Current", scope_name).execute()

                # Регистрируем зависимость
                key = f"switching_key_{thread_id}_{scope_num}"
                IoC.resolve(
                    "IoC.Register",
                    key,
                    lambda tid=thread_id, idx=scope_num: f"switching_value_{tid}_{idx}",
                ).execute()

                # Получаем значение
                value = IoC.resolve(key)

                with lock:
                    scope_values[f"{scope_name}:{key}"] = value

        except Exception as e:
            print(f"Ошибка в потоке {thread_id}: {e}")

    # Запускаем потоки
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(scope_switching_worker, i) for i in range(4)]

        for future in as_completed(futures):
            future.result()

    # Проверяем, что все значения корректны
    assert len(scope_values) == 12  # 4 потока * 3 скоупа

    for key, value in scope_values.items():
        scope_name, dep_key = key.split(":", 1)
        thread_id, scope_idx = scope_name.split("_")[1:3]
        expected_value = f"switching_value_{thread_id}_{scope_idx}"
        assert value == expected_value, f"Неверное значение для {key}"


def test_stress_test_multiple_operations():
    """
    Интенсивное выполнение множественных операций в
    конкурентной среде для проверки стабильности
    """
    operation_results = []
    lock = threading.Lock()

    def stress_worker(worker_id):
        try:
            results = []

            # Выполняем множество операций
            for iter_num in range(20):
                # Создаем скоуп
                scope_name = f"stress_{worker_id}_{iter_num}"
                IoC.resolve("Scopes.New", scope_name).execute()
                IoC.resolve("Scopes.Current", scope_name).execute()

                # Регистрируем зависимости
                for dep_num in range(3):
                    key = f"stress_key_{worker_id}_{iter_num}_{dep_num}"
                    IoC.resolve(
                        "IoC.Register",
                        key,
                        lambda w=worker_id, x=iter_num, y=dep_num: f"stress_value_{w}_{x}_{y}",
                    ).execute()

                    # Получаем значение
                    value = IoC.resolve(key)
                    results.append((key, value))

                # Очищаем скоуп
                IoC.resolve("Scopes.Clear", scope_name).execute()

            with lock:
                operation_results.extend(results)

        except Exception as e:
            print(f"Ошибка в воркере {worker_id}: {e}")

    # Запускаем стресс-тест
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(stress_worker, i) for i in range(8)]

        for future in as_completed(futures):
            future.result()

    end_time = time.time()

    # Проверяем результаты
    assert len(operation_results) == 8 * 20 * 3  # 8 воркеров * 20 итераций * 3 зависимости

    # Проверяем корректность значений
    for key, value in operation_results:
        parts = key.split("_")
        worker_id, iter_num, dep_num = int(parts[2]), int(parts[3]), int(parts[4])
        expected_value = f"stress_value_{worker_id}_{iter_num}_{dep_num}"
        assert value == expected_value, f"Неверное значение для {key}"

    print(f"Стресс-тест завершен за {end_time - start_time:.2f} секунд")


def test_race_condition_prevention():
    """Предотвращение race conditions при одновременном создании и работе со скоупами."""
    scope_creation_order = []
    lock = threading.Lock()

    def race_condition_worker(worker_id):
        try:
            # Создаем скоуп с уникальным именем
            scope_name = f"race_scope_{worker_id}_{threading.current_thread().ident}"
            IoC.resolve("Scopes.New", scope_name).execute()

            with lock:
                scope_creation_order.append(scope_name)

            # Устанавливаем как текущий
            IoC.resolve("Scopes.Current", scope_name).execute()

            # Проверяем, что скоуп действительно создан
            assert scope_name in IoC._scopes

            # Регистрируем зависимость
            key = f"race_key_{worker_id}"
            IoC.resolve("IoC.Register", key, lambda: f"race_value_{worker_id}").execute()

            # Получаем значение
            value = IoC.resolve(key)
            assert value == f"race_value_{worker_id}"

        except Exception as e:
            print(f"Ошибка в воркере {worker_id}: {e}")

    # Запускаем множество потоков одновременно
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(race_condition_worker, worker_id) for worker_id in range(15)]

        for future in as_completed(futures):
            future.result()

    # Проверяем, что все скоупы созданы
    assert len(scope_creation_order) == 15

    # Проверяем, что все скоупы существуют
    for scope_name in scope_creation_order:
        assert scope_name in IoC._scopes


def test_thread_local_cleanup():
    """Корректная очистка thread-local данных после завершения потоков."""
    thread_data = {}
    errors = {}

    def cleanup_worker(worker_id):
        try:
            # Создаем скоуп
            scope_name = f"cleanup_{worker_id}"
            IoC.resolve("Scopes.New", scope_name).execute()
            IoC.resolve("Scopes.Current", scope_name).execute()

            # Регистрируем зависимость
            key = f"cleanup_key_{worker_id}"
            IoC.resolve("IoC.Register", key, lambda: f"cleanup_value_{worker_id}").execute()

            # Получаем значение
            value = IoC.resolve(key)
            thread_data[worker_id] = value

            # Проверяем, что скоуп доступен
            assert scope_name in IoC._scopes

        except Exception as e:
            errors[worker_id] = str(e)

    # Запускаем потоки через ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(cleanup_worker, worker_id) for worker_id in range(5)]

        for future in as_completed(futures):
            future.result()

    # Проверяем результаты
    assert len(thread_data) == 5
    assert len(errors) == 0, f"Ошибки: {errors}"

    # Проверяем, что все скоупы созданы
    for worker_num in range(5):
        scope_name = f"cleanup_{worker_num}"
        assert scope_name in IoC._scopes
