# -*- coding: utf-8 -*-
# report_protection.py - Protected Report Generation for Demo Mode
import logging
from datetime import date, datetime
import os

def create_protected_report_for_period(start_date: date, end_date: date):
    """Создает защищенный отчет за период (демо версия)."""
    try:
        # Импортируем демо данные
        try:
            from database_demo import monitoring_checks, DEMO_STORES, DEMO_NETWORKS, DEMO_REGIONS
        except ImportError:
            from database import get_checked_stores_for_date
            logging.error("Демо данные недоступны")
            return None
        
        # Создаем CSV отчет за период
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/Защищенный_отчет_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}_{timestamp}.csv"
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Заголовок отчета
            f.write(f"Защищенный отчет за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}\n")
            f.write(f"Создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Заголовки CSV
            f.write("Дата,Регион,Сеть,Магазин,Адрес,Товар,Наличие,Обычная цена,Акционная цена,Есть акция,Остаток\n")
            
            # Собираем данные за период
            current_date = start_date
            total_checks = 0
            
            while current_date <= end_date:
                date_str = current_date.isoformat()
                
                # Проходим по всем проверкам за эту дату
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
                            from database_demo import price_checks
                            price_key = f"{store_id}_{product}_{date_str}"
                            price_data = price_checks.get(price_key, {})
                            
                            status = "Да" if is_present else "Нет"
                            regular_price = price_data.get('regular_price', '')
                            promo_price = price_data.get('promo_price', '')
                            has_promo = "Да" if price_data.get('has_promo') else "Нет"
                            stock = price_data.get('stock_quantity', '')
                            
                            f.write(f'"{current_date.strftime("%d.%m.%Y")}","{region_name}","{network_name}","№{store_info[1]}","{store_info[2]}","{product}","{status}","{regular_price}","{promo_price}","{has_promo}","{stock}"\n')
                            total_checks += 1
                
                # Переходим к следующему дню
                from datetime import timedelta
                current_date += timedelta(days=1)
            
            # Добавляем итоги
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Всего проверок: {total_checks}\n")
            f.write(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n")
        
        logging.info(f"Создан защищенный отчет за период: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Ошибка создания защищенного отчета: {e}")
        return None

def create_today_report():
    """Создает отчет за сегодня."""
    today = date.today()
    return create_protected_report_for_period(today, today)