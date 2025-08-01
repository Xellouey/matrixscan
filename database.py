# -*- coding: utf-8 -*-
# database.py - Web App Database Module
import sqlite3
import logging
from datetime import date, datetime
import pandas as pd
import os

# --- Инициализация соединения с БД ---
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def get_all_regions():
    """Получает все регионы из базы данных."""
    cursor.execute("SELECT id, name FROM regions ORDER BY name")
    return cursor.fetchall()

def get_networks_by_region(region_id: int):
    """Получает все сети для указанного региона."""
    cursor.execute("SELECT id, name FROM networks WHERE region_id = ? ORDER BY name", (region_id,))
    return cursor.fetchall()

def get_stores_by_network(network_id: int):
    """Получает все магазины для указанной сети."""
    cursor.execute("SELECT id, number, address FROM stores WHERE network_id = ? ORDER BY number", (network_id,))
    return cursor.fetchall()

def get_checked_stores_for_date(check_date: date):
    """Получает список ID магазинов, которые были проверены в указанную дату."""
    cursor.execute("""
        SELECT DISTINCT store_id 
        FROM monitoring_checks 
        WHERE check_date = ?
    """, (check_date,))
    return {row[0] for row in cursor.fetchall()}

def get_nomenclature_by_store_id(store_id: int):
    """Получает номенклатуру для указанного магазина."""
    cursor.execute("""
        SELECT product_name 
        FROM nomenclature 
        WHERE store_id = ? 
        ORDER BY product_name
    """, (store_id,))
    return cursor.fetchall()

def get_checked_items_for_store_date(store_id: int, check_date: date):
    """Получает отмеченные товары для магазина на указанную дату."""
    cursor.execute("""
        SELECT product_name 
        FROM monitoring_checks 
        WHERE store_id = ? AND check_date = ? AND is_present = 1
    """, (store_id, check_date))
    return {row[0] for row in cursor.fetchall()}

def record_check_results(store_id: int, all_products: list, checked_products: set, check_date: date):
    """Записывает результаты проверки в базу данных."""
    try:
        # Удаляем старые записи за эту дату для этого магазина
        cursor.execute("""
            DELETE FROM monitoring_checks 
            WHERE store_id = ? AND check_date = ?
        """, (store_id, check_date))
        
        # Записываем новые результаты
        for product in all_products:
            is_present = 1 if product in checked_products else 0
            cursor.execute("""
                INSERT INTO monitoring_checks (store_id, product_name, check_date, is_present)
                VALUES (?, ?, ?, ?)
            """, (store_id, product, check_date, is_present))
        
        conn.commit()
        logging.info(f"Записаны результаты проверки для магазина {store_id}: {len(checked_products)}/{len(all_products)}")
        return True
    except Exception as e:
        logging.error(f"Ошибка записи результатов проверки: {e}")
        conn.rollback()
        return False

def find_stores_in_network(network_id: int, query: str):
    """Ищет магазины по номеру или части адреса в указанной сети."""
    try:
        cursor.execute("""
            SELECT id, number, address 
            FROM stores 
            WHERE network_id = ? AND (
                LOWER(CAST(number AS TEXT)) LIKE LOWER(?) OR 
                LOWER(address) LIKE LOWER(?)
            )
            ORDER BY number
            LIMIT 20
        """, (network_id, f"%{query}%", f"%{query}%"))
        
        results = []
        for store in cursor.fetchall():
            results.append({
                'id': store[0],
                'number': store[1],
                'address': store[2] or 'Адрес не указан'
            })
        
        return results
    except Exception as e:
        logging.error(f"Ошибка поиска магазинов: {e}")
        return []

def save_price_check(store_id: int, product_name: str, check_date: date, 
                    regular_price: float = None, promo_price: float = None, 
                    has_promo: bool = False, stock_quantity: int = None):
    """Сохраняет данные о проверке цены товара."""
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO price_checks 
            (store_id, product_name, check_date, regular_price, promo_price, has_promo, stock_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (store_id, product_name, check_date, regular_price, promo_price, has_promo, stock_quantity))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения проверки цены: {e}")
        return False

def get_price_check(store_id: int, product_name: str, check_date: date):
    """Получает данные о проверке цены товара."""
    cursor.execute("""
        SELECT regular_price, promo_price, has_promo, stock_quantity
        FROM price_checks 
        WHERE store_id = ? AND product_name = ? AND check_date = ?
    """, (store_id, product_name, check_date))
    
    result = cursor.fetchone()
    if result:
        return {
            'regular_price': result[0],
            'promo_price': result[1],
            'has_promo': result[2],
            'stock_quantity': result[3]
        }
    return None

def create_store_report(store_id: int, report_date: date, store_name: str = None):
    """Создает Excel отчет для магазина."""
    try:
        import pandas as pd
        from datetime import datetime
        
        # Получаем данные проверки
        cursor.execute("""
            SELECT mc.product_name, mc.is_present,
                   pc.regular_price, pc.promo_price, pc.has_promo, pc.stock_quantity
            FROM monitoring_checks mc
            LEFT JOIN price_checks pc ON mc.store_id = pc.store_id 
                AND mc.product_name = pc.product_name 
                AND mc.check_date = pc.check_date
            WHERE mc.store_id = ? AND mc.check_date = ?
            ORDER BY mc.product_name
        """, (store_id, report_date))
        
        data = cursor.fetchall()
        
        if not data:
            logging.warning(f"Нет данных для отчета магазина {store_id} за {report_date}")
            return None
        
        # Создаем DataFrame
        df_data = []
        for row in data:
            df_data.append({
                'Товар': row[0],
                'Наличие': 'Да' if row[1] else 'Нет',
                'Обычная цена': row[2] if row[2] else '',
                'Акционная цена': row[3] if row[3] else '',
                'Есть акция': 'Да' if row[4] else 'Нет',
                'Остаток': row[5] if row[5] else ''
            })
        
        df = pd.DataFrame(df_data)
        
        # Создаем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/Отчет_магазин_{store_id}_{report_date.strftime('%Y-%m-%d')}_{timestamp}.xlsx"
        
        # Создаем папку reports если её нет
        os.makedirs('reports', exist_ok=True)
        
        # Сохраняем в Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Отчет', index=False)
        
        logging.info(f"Создан отчет: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Ошибка создания отчета: {e}")
        return None

def create_tables_if_not_exist():
    """Создает таблицы в базе данных, если они не существуют."""
    try:
        # Таблица регионов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Таблица сетей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region_id INTEGER,
                FOREIGN KEY (region_id) REFERENCES regions (id)
            )
        """)
        
        # Таблица магазинов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                address TEXT,
                network_id INTEGER,
                FOREIGN KEY (network_id) REFERENCES networks (id)
            )
        """)
        
        # Таблица номенклатуры
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nomenclature (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER,
                product_name TEXT NOT NULL,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        # Таблица результатов мониторинга
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER,
                product_name TEXT NOT NULL,
                check_date DATE NOT NULL,
                is_present INTEGER DEFAULT 0,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        # Таблица проверок цен
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER,
                product_name TEXT NOT NULL,
                check_date DATE NOT NULL,
                regular_price REAL,
                promo_price REAL,
                has_promo INTEGER DEFAULT 0,
                stock_quantity INTEGER,
                FOREIGN KEY (store_id) REFERENCES stores (id),
                UNIQUE(store_id, product_name, check_date)
            )
        """)
        
        conn.commit()
        logging.info("Таблицы базы данных проверены/созданы")
        
    except Exception as e:
        logging.error(f"Ошибка создания таблиц: {e}")