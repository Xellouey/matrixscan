# -*- coding: utf-8 -*-
# database_demo.py - Demo Database Module for Vercel
import logging
from datetime import date, datetime
import os

# Демо данные для тестирования
DEMO_REGIONS = [
    (1, "СЗФО"),
    (2, "ЦФО"),
    (3, "ЮФО")
]

DEMO_NETWORKS = [
    (1, "Розница", 1),
    (2, "Магнит", 1),
    (3, "Пятерочка", 2),
    (4, "Лента", 3)
]

DEMO_STORES = [
    # Розница (network_id = 1)
    (1, "001", "ул. Ленина, 1", 1),
    (2, "002", "пр. Мира, 15", 1),
    (3, "003", "ул. Советская, 22", 1),
    (8, "004", "ул. Комсомольская, 45", 1),
    (9, "005", "пр. Строителей, 12", 1),
    
    # Магнит (network_id = 2)
    (4, "101", "ул. Пушкина, 5", 2),
    (5, "102", "пр. Победы, 8", 2),
    (10, "103", "ул. Молодежная, 33", 2),
    (11, "104", "пр. Космонавтов, 67", 2),
    
    # Пятерочка (network_id = 3)
    (6, "201", "ул. Гагарина, 12", 3),
    (12, "202", "ул. Рабочая, 89", 3),
    (13, "203", "пр. Ветеранов, 23", 3),
    
    # Лента (network_id = 4)
    (7, "301", "ул. Кирова, 7", 4),
    (14, "302", "пр. Энгельса, 156", 4),
    (15, "303", "ул. Дружбы, 78", 4)
]

# Базовая номенклатура для всех магазинов
BASE_NOMENCLATURE = ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Сыр российский", "Колбаса докторская", "Творог 9%", "Кефир 1%", "Сметана 20%", "Йогурт натуральный", "Ряженка"]

DEMO_NOMENCLATURE = {
    # Розница
    1: BASE_NOMENCLATURE + ["Сосиски", "Майонез", "Хлеб черный"],
    2: BASE_NOMENCLATURE + ["Батон", "Сливки 10%", "Сыр плавленый"],
    3: BASE_NOMENCLATURE + ["Простокваша", "Масло растительное", "Сыр твердый"],
    8: BASE_NOMENCLATURE + ["Сосиски", "Творожок детский", "Молоко 2.5%"],
    9: BASE_NOMENCLATURE + ["Кефир 2.5%", "Сметана 15%", "Йогурт питьевой"],
    
    # Магнит
    4: BASE_NOMENCLATURE + ["Сосиски", "Творожная масса", "Молоко топленое"],
    5: BASE_NOMENCLATURE + ["Ряженка 4%", "Сыр адыгейский", "Масло топленое"],
    10: BASE_NOMENCLATURE + ["Кефир детский", "Творог зерненый", "Йогурт греческий"],
    11: BASE_NOMENCLATURE + ["Сметана домашняя", "Молоко безлактозное", "Сыр моцарелла"],
    
    # Пятерочка
    6: BASE_NOMENCLATURE + ["Творожок глазированный", "Кефир био", "Молоко органическое"],
    12: BASE_NOMENCLATURE + ["Ряженка домашняя", "Сыр фета", "Йогурт без добавок"],
    13: BASE_NOMENCLATURE + ["Сметана фермерская", "Творог обезжиренный", "Кефир 3.2%"],
    
    # Лента
    7: BASE_NOMENCLATURE + ["Молоко козье", "Сыр камамбер", "Творог домашний"],
    14: BASE_NOMENCLATURE + ["Ряженка органическая", "Йогурт пробиотик", "Кефир тибетский"],
    15: BASE_NOMENCLATURE + ["Сметана органическая", "Творог фермерский", "Молоко фермерское"]
}

# Хранилище для проверок (в памяти)
monitoring_checks = {}
price_checks = {}

def get_all_regions():
    """Получает все регионы из демо данных."""
    return DEMO_REGIONS

def get_networks_by_region(region_id: int):
    """Получает все сети для указанного региона."""
    return [(net_id, name) for net_id, name, reg_id in DEMO_NETWORKS if reg_id == region_id]

def get_stores_by_network(network_id: int):
    """Получает все магазины для указанной сети."""
    return [(store_id, number, address) for store_id, number, address, net_id in DEMO_STORES if net_id == network_id]

def get_checked_stores_for_date(check_date: date):
    """Получает список ID магазинов, которые были проверены в указанную дату."""
    date_str = check_date.isoformat()
    return {store_id for store_id, checks in monitoring_checks.items() 
            if date_str in checks}

def get_nomenclature_by_store_id(store_id: int):
    """Получает номенклатуру для указанного магазина."""
    products = DEMO_NOMENCLATURE.get(store_id, [])
    return [(product,) for product in products]

def get_checked_items_for_store_date(store_id: int, check_date: date):
    """Получает отмеченные товары для магазина на указанную дату."""
    date_str = check_date.isoformat()
    store_checks = monitoring_checks.get(store_id, {})
    date_checks = store_checks.get(date_str, {})
    return {product for product, is_present in date_checks.items() if is_present}

def record_check_results(store_id: int, all_products: list, checked_products: set, check_date: date):
    """Записывает результаты проверки в память."""
    try:
        date_str = check_date.isoformat()
        
        if store_id not in monitoring_checks:
            monitoring_checks[store_id] = {}
        
        monitoring_checks[store_id][date_str] = {}
        
        for product in all_products:
            is_present = product in checked_products
            monitoring_checks[store_id][date_str][product] = is_present
        
        logging.info(f"Записаны результаты проверки для магазина {store_id}: {len(checked_products)}/{len(all_products)}")
        return True
    except Exception as e:
        logging.error(f"Ошибка записи результатов проверки: {e}")
        return False

def find_stores_in_network(network_id: int, query: str):
    """Ищет магазины по номеру или части адреса в указанной сети."""
    try:
        results = []
        query_lower = query.lower()
        
        for store_id, number, address, net_id in DEMO_STORES:
            if net_id == network_id:
                if (query_lower in str(number).lower() or 
                    query_lower in (address or '').lower()):
                    results.append({
                        'id': store_id,
                        'number': number,
                        'address': address or 'Адрес не указан'
                    })
        
        return results[:20]  # Ограничиваем до 20 результатов
    except Exception as e:
        logging.error(f"Ошибка поиска магазинов: {e}")
        return []

def save_price_check(store_id: int, product_name: str, check_date: date, 
                    regular_price: float = None, promo_price: float = None, 
                    has_promo: bool = False, stock_quantity: int = None, 
                    price_notes: str = None):
    """Сохраняет данные о проверке цены товара в память."""
    try:
        date_str = check_date.isoformat()
        key = f"{store_id}_{product_name}_{date_str}"
        
        price_checks[key] = {
            'regular_price': regular_price,
            'promo_price': promo_price,
            'has_promo': has_promo,
            'stock_quantity': stock_quantity,
            'price_notes': price_notes or ''
        }
        
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения проверки цены: {e}")
        return False

def get_price_check(store_id: int, product_name: str, check_date: date):
    """Получает данные о проверке цены товара."""
    date_str = check_date.isoformat()
    key = f"{store_id}_{product_name}_{date_str}"
    price_data = price_checks.get(key)
    if price_data:
        # Добавляем price_notes для совместимости
        price_data = price_data.copy()
        price_data['price_notes'] = price_data.get('price_notes', '')
    return price_data

def create_store_report(store_id: int, report_date: date, store_name: str = None):
    """Создает отчет для магазина (демо версия - только текстовый формат)."""
    try:
        from datetime import datetime
        import os
        
        # Получаем данные проверки из памяти
        date_str = report_date.isoformat()
        store_checks = monitoring_checks.get(store_id, {})
        date_checks = store_checks.get(date_str, {})
        
        if not date_checks:
            logging.warning(f"Нет данных для отчета магазина {store_id} за {report_date}")
            return None
        
        # Создаем простой CSV отчет (совместимый с Excel)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/Отчет_магазин_{store_id}_{report_date.strftime('%Y-%m-%d')}_{timestamp}.csv"
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Заголовки CSV
            f.write("Товар,Наличие,Обычная цена,Акционная цена,Есть акция,Остаток\n")
            
            # Данные
            for product, is_present in date_checks.items():
                price_key = f"{store_id}_{product}_{date_str}"
                price_data = price_checks.get(price_key, {})
                
                status = "Да" if is_present else "Нет"
                regular_price = price_data.get('regular_price', '')
                promo_price = price_data.get('promo_price', '')
                has_promo = "Да" if price_data.get('has_promo') else "Нет"
                stock = price_data.get('stock_quantity', '')
                
                f.write(f'"{product}","{status}","{regular_price}","{promo_price}","{has_promo}","{stock}"\n')
        
        logging.info(f"Создан CSV отчет: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Ошибка создания отчета: {e}")
        return None

def create_tables_if_not_exist():
    """Заглушка для совместимости."""
    logging.info("Демо режим: таблицы не требуются")
    pass

def create_today_report():
    """Создает отчет за сегодня (демо версия)."""
    try:
        from datetime import datetime
        import os
        
        today = date.today()
        date_str = today.isoformat()
        
        # Создаем CSV отчет за сегодня
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/Отчет_за_сегодня_{today.strftime('%Y-%m-%d')}_{timestamp}.csv"
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Заголовок отчета
            f.write(f"Отчет за {today.strftime('%d.%m.%Y')}\n")
            f.write(f"Создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Заголовки CSV
            f.write("Регион,Сеть,Магазин,Адрес,Товар,Наличие,Обычная цена,Акционная цена,Есть акция,Остаток\n")
            
            total_checks = 0
            
            # Проходим по всем проверкам за сегодня
            for store_id, store_checks in monitoring_checks.items():
                if date_str in store_checks:
                    # Получаем информацию о магазине
                    store_info = next((s for s in DEMO_STORES if s[0] == store_id), None)
                    if not store_info:
                        continue
                        
                    # Получаем информацию о сети
                    network_info = next((n for n in DEMO_NETWORKS if n[0] == store_info[3]), None)
                    network_name = network_info[1] if network_info else "Неизвестная сеть"
                    
                    # Получаем информацию о регионе
                    region_info = next((r for r in DEMO_REGIONS if r[0] == (network_info[2] if network_info else 1)), None)
                    region_name = region_info[1] if region_info else "Неизвестный регион"
                    
                    # Записываем данные по каждому товару
                    date_checks = store_checks[date_str]
                    for product, is_present in date_checks.items():
                        # Получаем данные о ценах
                        price_key = f"{store_id}_{product}_{date_str}"
                        price_data = price_checks.get(price_key, {})
                        
                        status = "Да" if is_present else "Нет"
                        regular_price = price_data.get('regular_price', '')
                        promo_price = price_data.get('promo_price', '')
                        has_promo = "Да" if price_data.get('has_promo') else "Нет"
                        stock = price_data.get('stock_quantity', '')
                        
                        f.write(f'"{region_name}","{network_name}","№{store_info[1]}","{store_info[2]}","{product}","{status}","{regular_price}","{promo_price}","{has_promo}","{stock}"\n')
                        total_checks += 1
            
            # Добавляем итоги
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Всего проверок: {total_checks}\n")
            f.write(f"Дата: {today.strftime('%d.%m.%Y')}\n")
        
        logging.info(f"Создан отчет за сегодня: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Ошибка создания отчета за сегодня: {e}")
        return None

# Инициализация для совместимости
conn = None
cursor = None

def get_last_price_in_network(network_id: int, product_name: str):
    """Получает последнюю цену товара в сети (демо версия)."""
    try:
        from datetime import date
        
        # Ищем последнюю цену в наших данных
        today = date.today()
        date_str = today.isoformat()
        
        # Получаем все магазины сети
        network_stores = [store_id for store_id, number, address, net_id in DEMO_STORES if net_id == network_id]
        
        # Ищем последнюю цену среди всех магазинов сети
        for store_id in network_stores:
            price_key = f"{store_id}_{product_name}_{date_str}"
            if price_key in price_checks:
                price_data = price_checks[price_key]
                store_info = next((s for s in DEMO_STORES if s[0] == store_id), None)
                
                return {
                    'regular_price': price_data.get('regular_price'),
                    'promo_price': price_data.get('promo_price'),
                    'has_promo': price_data.get('has_promo', False),
                    'check_date': date_str,
                    'store_number': store_info[1] if store_info else 'Неизвестно'
                }
        
        return None
        
    except Exception as e:
        logging.error(f"Ошибка получения последней цены: {e}")
        return None

def create_sample_data():
    """Создает образцы данных для демонстрации."""
    from datetime import date, timedelta
    import random
    
    # Создаем данные за последние 3 дня
    today = date.today()
    
    for days_ago in range(3):
        check_date = today - timedelta(days=days_ago)
        date_str = check_date.isoformat()
        
        # Для каждого магазина создаем случайные проверки
        for store_id in [1, 2, 4, 6, 7]:  # Выборочно несколько магазинов
            if store_id not in monitoring_checks:
                monitoring_checks[store_id] = {}
            
            if date_str not in monitoring_checks[store_id]:
                monitoring_checks[store_id][date_str] = {}
            
            # Получаем номенклатуру магазина
            store_products = DEMO_NOMENCLATURE.get(store_id, BASE_NOMENCLATURE)
            
            # Случайно отмечаем товары как присутствующие/отсутствующие
            for product in store_products[:7]:  # Берем первые 7 товаров
                is_present = random.choice([True, True, True, False])  # 75% вероятность наличия
                monitoring_checks[store_id][date_str][product] = is_present
                
                # Если товар присутствует, добавляем цену
                if is_present:
                    price_key = f"{store_id}_{product}_{date_str}"
                    regular_price = random.randint(50, 500)  # Цена от 50 до 500 рублей
                    has_promo = random.choice([True, False])
                    promo_price = regular_price - random.randint(10, 50) if has_promo else None
                    stock = random.randint(5, 100)
                    
                    price_checks[price_key] = {
                        'regular_price': regular_price,
                        'promo_price': promo_price,
                        'has_promo': has_promo,
                        'stock_quantity': stock,
                        'price_notes': f'Проверено {check_date.strftime("%d.%m.%Y")}'
                    }
    
    logging.info(f"Созданы образцы данных за {len(monitoring_checks)} магазинов за 3 дня")

# Создаем образцы данных при импорте модуля
create_sample_data()