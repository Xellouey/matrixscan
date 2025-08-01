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
    (1, "001", "ул. Ленина, 1", 1),
    (2, "002", "пр. Мира, 15", 1),
    (3, "003", "ул. Советская, 22", 1),
    (4, "101", "ул. Пушкина, 5", 2),
    (5, "102", "пр. Победы, 8", 2),
    (6, "201", "ул. Гагарина, 12", 3),
    (7, "301", "ул. Кирова, 7", 4)
]

DEMO_NOMENCLATURE = {
    1: ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Сыр российский", "Колбаса докторская"],
    2: ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Творог 9%", "Йогурт натуральный"],
    3: ["Хлеб белый", "Молоко 3.2%", "Кефир 1%", "Сметана 20%", "Ряженка"],
    4: ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Сыр российский", "Творог 9%"],
    5: ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Колбаса докторская", "Сосиски"],
    6: ["Хлеб белый", "Молоко 3.2%", "Кефир 1%", "Творог 9%", "Йогурт натуральный"],
    7: ["Хлеб белый", "Молоко 3.2%", "Масло сливочное", "Сыр российский", "Сметана 20%"]
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
                    has_promo: bool = False, stock_quantity: int = None):
    """Сохраняет данные о проверке цены товара в память."""
    try:
        date_str = check_date.isoformat()
        key = f"{store_id}_{product_name}_{date_str}"
        
        price_checks[key] = {
            'regular_price': regular_price,
            'promo_price': promo_price,
            'has_promo': has_promo,
            'stock_quantity': stock_quantity
        }
        
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения проверки цены: {e}")
        return False

def get_price_check(store_id: int, product_name: str, check_date: date):
    """Получает данные о проверке цены товара."""
    date_str = check_date.isoformat()
    key = f"{store_id}_{product_name}_{date_str}"
    return price_checks.get(key)

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