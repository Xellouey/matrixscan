#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask сервер для Web App - Система мониторинга торговых сетей
Standalone версия без зависимостей от Telegram бота
"""

from flask import Flask, render_template_string, jsonify, request, send_from_directory
import os
import json
from datetime import datetime, date
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Используем демо базу данных для Vercel
try:
    from database_demo import get_checked_stores_for_date, get_all_regions, get_networks_by_region, get_stores_by_network, get_last_price_in_network, save_price_check, get_price_check
    logger.info("Используется демо база данных")
except ImportError:
    from database import get_checked_stores_for_date, get_all_regions, get_networks_by_region, get_stores_by_network, get_last_price_in_network, save_price_check, get_price_check
    logger.info("Используется локальная база данных")

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

@app.route('/')
def index():
    """Главная страница Web App"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return "Web App файл не найден", 404

@app.route('/manifest.json')
def manifest():
    """PWA Manifest файл"""
    try:
        with open('manifest.json', 'r', encoding='utf-8') as f:
            manifest_content = f.read()
        return manifest_content, 200, {'Content-Type': 'application/json'}
    except FileNotFoundError:
        return "Manifest не найден", 404

@app.route('/sw.js')
def service_worker():
    """Service Worker файл"""
    try:
        with open('sw.js', 'r', encoding='utf-8') as f:
            sw_content = f.read()
        return sw_content, 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "Service Worker не найден", 404

@app.route('/icon-<int:size>.png')
def pwa_icon(size):
    """PWA иконки"""
    try:
        return send_from_directory('.', f'icon-{size}.png')
    except FileNotFoundError:
        return "Иконка не найдена", 404

@app.route('/icon-<int:size>-maskable.png')
def pwa_maskable_icon(size):
    """PWA maskable иконки"""
    try:
        return send_from_directory('.', f'icon-{size}-maskable.png')
    except FileNotFoundError:
        return "Maskable иконка не найдена", 404

@app.route('/test')
def test_page():
    """Простая тестовая страница"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Тест кнопки и Excel отчета</title>
</head>
<body>
    <h1>🧪 Тест API и Excel отчета</h1>
    <button onclick="testButton()" style="padding: 20px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 10px;">
        📤 Тест save-and-send
    </button>
    <button onclick="testExcel()" style="padding: 20px; font-size: 16px; background: #FF9800; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 10px;">
        📊 Тест Excel отчета
    </button>
    <div id="result" style="margin-top: 20px; padding: 10px; background: #f0f0f0; font-family: monospace;"></div>
    
    <script>
        function log(msg) {
            document.getElementById('result').innerHTML += msg + '<br>';
        }
        
        function clear() {
            document.getElementById('result').innerHTML = '';
        }
        
        async function testButton() {
            clear();
            log('🖱️ Тест save-and-send начат!');
            
            try {
                const response = await fetch('/api/save-and-send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        store_id: 1,
                        store_name: 'Тестовый магазин',
                        checked_items: ['товар1', 'товар2'],
                        total_items: 10
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    log('✅ save-and-send работает: ' + data.message);
                } else {
                    log('❌ Ошибка save-and-send: ' + data.error);
                }
                
            } catch (error) {
                log('💥 Ошибка: ' + error.message);
            }
        }
        
        async function testExcel() {
            clear();
            log('📊 Тест создания Excel отчета начат!');
            
            try {
                const response = await fetch('/api/send-to-telegram', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: 'Тест Excel отчета',
                        store_id: 1,
                        store_name: 'Тестовый магазин'
                    })
                });
                
                log('📥 Ответ: HTTP ' + response.status);
                
                const data = await response.json();
                log('📄 Данные: ' + JSON.stringify(data, null, 2));
                
                if (data.success && data.report_file) {
                    log('✅ Excel отчет создан: ' + data.report_file);
                } else {
                    log('❌ Excel отчет НЕ создан');
                }
                
            } catch (error) {
                log('💥 Ошибка: ' + error.message);
            }
        }
        
        log('🚀 Тестовая страница загружена');
        log('📋 Нажмите кнопки для тестирования');
    </script>
</body>
</html>
    '''

@app.route('/api/save-and-send', methods=['POST'])
def save_and_send():
    """API для сохранения и отправки данных"""
    try:
        data = request.get_json()
        
        # Проверяем обязательные поля
        if not data:
            return jsonify({
                'success': False,
                'error': 'Нет данных для сохранения'
            }), 400
            
        store_id = data.get('store_id')
        store_name = data.get('store_name')
        checked_items = data.get('checked_items', [])
        total_items = data.get('total_items', 0)
        
        if not store_id or not store_name:
            return jsonify({
                'success': False,
                'error': 'Не указан ID или название магазина'
            }), 400
        
        logger.info(f"Сохранение и отправка для магазина {store_name} (ID: {store_id}): {len(checked_items)}/{total_items}")
        
        # Сохраняем данные в базу
        try:
            from database_demo import record_check_results, get_nomenclature_by_store_id
        except ImportError:
            from database import record_check_results, get_nomenclature_by_store_id
        from datetime import date
        
        try:
            # Получаем всю номенклатуру магазина
            all_nomenclature = get_nomenclature_by_store_id(store_id)
            all_products = [item[0] for item in all_nomenclature]  # item[0] это product_name
            
            if not all_products:
                return jsonify({
                    'success': False,
                    'error': f'Номенклатура для магазина {store_name} не найдена'
                }), 404
            
            # Сохраняем результаты мониторинга
            today = date.today()
            record_check_results(store_id, all_products, set(checked_items), today)
            
            logger.info(f"Данные успешно сохранены для магазина {store_id}")
            
            return jsonify({
                'success': True,
                'message': f'Данные сохранены для магазина {store_name}. Проверено: {len(checked_items)} из {len(all_products)} товаров'
            })
            
        except Exception as db_error:
            logger.error(f"Ошибка сохранения в БД: {db_error}")
            return jsonify({
                'success': False,
                'error': f'Ошибка сохранения в базу данных: {str(db_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Ошибка в save_and_send: {e}")
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/send-to-telegram', methods=['POST'])
def send_to_telegram():
    """API для отправки сообщений и файлов в Telegram"""
    try:
        # Импорты в начале функции
        try:
            from database_demo import create_store_report
        except ImportError:
            from database import create_store_report
        from datetime import date
        import os
        
        data = request.get_json()
        message = data.get('message', '')
        store_id = data.get('store_id')
        store_name = data.get('store_name', 'Неизвестный магазин')
        inspector_name = data.get('inspector_name', '')
        comment = data.get('comment', '')
        
        logger.info(f"Создание и отправка отчета для магазина {store_name} (проверил: {inspector_name})")
        
        # Получаем подробную информацию о магазине
        store_info = get_store_details(store_id)
        
        # Создаем расширенное сообщение с адресом
        if store_info:
            enhanced_message = f"""📋 Отчет по проверке номенклатуры

🏪 Магазин: {store_info.get('name', store_name)}
📍 Адрес: {store_info.get('address', 'Адрес не указан')}
🆔 ID магазина: {store_id}
📅 Дата проверки: {date.today().strftime('%d.%m.%Y')}
👤 Проверил: {inspector_name}
📊 Результат: проверка завершена"""
            
            if comment:
                enhanced_message += f"\n\n💬 Комментарий: {comment}"
                
            message = enhanced_message
        
        # Создаем Excel отчет
        
        try:
            today = date.today()
            report_filename = create_store_report(store_id, today, store_name)
            
            if report_filename and os.path.exists(report_filename):
                logger.info(f"Excel отчет создан: {report_filename}")
                
                # Отправляем в Telegram
                telegram_success = send_report_to_telegram(report_filename, message, comment)
                
                if telegram_success:
                    return jsonify({
                        'success': True,
                        'message': f'Отчет создан и отправлен в Telegram: {os.path.basename(report_filename)}',
                        'report_file': report_filename
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': f'Отчет создан, но не удалось отправить в Telegram: {os.path.basename(report_filename)}',
                        'report_file': report_filename
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось создать отчет'
                }), 500
                
        except Exception as report_error:
            logger.error(f"Ошибка создания отчета: {report_error}")
            return jsonify({
                'success': False,
                'error': f'Ошибка создания отчета: {str(report_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Ошибка в send_to_telegram: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def send_report_to_telegram(report_filename, message, comment):
    """Отправляет отчет в Telegram группу"""
    try:
        import requests
        import os
        
        # Настройки бота из .env файла
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        CHAT_ID = os.getenv('MAIN_GROUP_ID')
        
        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Не настроены BOT_TOKEN или MAIN_GROUP_ID в .env файле")
            logger.info(f"Отчет создан локально: {report_filename}")
            logger.info(f"Сообщение: {message}")
            if comment:
                logger.info(f"Комментарий: {comment}")
            return False
        
        # Отправляем файл
        with open(report_filename, 'rb') as file:
            files = {'document': file}
            data = {
                'chat_id': CHAT_ID,
                'caption': message
            }
            
            response = requests.post(
                f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Отчет успешно отправлен в Telegram")
                return True
            else:
                logger.error(f"Ошибка отправки в Telegram: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False

def get_store_addresses_from_excel():
    """Получает словарь адресов магазинов из Excel файлов (демо версия)"""
    try:
        # В демо режиме возвращаем пустой словарь
        # В реальном приложении здесь была бы работа с Excel файлами
        logging.info("Демо режим: адреса из Excel недоступны")
        return {}
            
    except Exception as e:
        logging.error(f"Ошибка получения адресов из Excel: {e}")
        return {}

def get_store_details(store_id):
    """Получает подробную информацию о магазине из базы данных и Excel файлов"""
    try:
        try:
            from database_demo import DEMO_STORES, DEMO_NETWORKS
            # В демо режиме используем статические данные
            store_data = next((s for s in DEMO_STORES if s[0] == store_id), None)
            if not store_data:
                return None
                
            network_data = next((n for n in DEMO_NETWORKS if n[0] == store_data[3]), None)
            network_name = network_data[1] if network_data else "Неизвестная сеть"
            
            store_info = {
                'name': store_data[1],
                'address': store_data[2] or 'Адрес не указан',
                'network_name': network_name,
                'region_name': 'СЗФО'
            }
            
        except ImportError:
            from database import cursor
            
            # Получаем базовую информацию из БД
            cursor.execute("""
                SELECT s.number as name, s.address, n.name as network_name
                FROM stores s
                LEFT JOIN networks n ON s.network_id = n.id  
                WHERE s.id = ?
            """, (store_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
                
            store_info = {
                'name': result['name'],
                'address': result['address'] or 'Адрес не указан',
                'network_name': result['network_name'],
                'region_name': 'СЗФО'  # Из названий файлов видно что это СЗФО
            }
            
            # Получаем адрес из Excel файлов
            store_addresses = get_store_addresses_from_excel()
            if store_id in store_addresses:
                store_info['address'] = store_addresses[store_id]
                logger.info(f"Найден адрес для магазина {store_id}: {store_addresses[store_id]}")
        
        return store_info
            
    except Exception as e:
        logger.error(f"Ошибка получения информации о магазине {store_id}: {e}")
        return None

@app.route('/api/create-excel-report', methods=['POST'])
def create_professional_excel_report():
    """API для создания СТРОГО ЗАЩИЩЕННОГО профессионального Excel отчета"""
    try:
        from report_protection import create_protected_report_for_period
        from datetime import date
        import os
        
        data = request.get_json()
        store_id = data.get('store_id')
        store_name = data.get('store_name', 'Неизвестный магазин')
        checked_items = data.get('checked_items', [])
        total_items = data.get('total_items', 0)
        
        if not store_id or not store_name:
            return jsonify({
                'success': False,
                'error': 'Не указан ID или название магазина'
            }), 400
        
        logger.info(f"🛡️ СТРОГО ЗАЩИЩЕННОЕ создание Excel отчета для магазина {store_name} (ID: {store_id})")
        
        # Сначала сохраняем данные в базу
        try:
            from database_demo import record_check_results, get_nomenclature_by_store_id
        except ImportError:
            from database import record_check_results, get_nomenclature_by_store_id
        
        try:
            # Получаем всю номенклатуру магазина
            all_nomenclature = get_nomenclature_by_store_id(store_id)
            all_products = [item[0] for item in all_nomenclature]  # item[0] это product_name
            
            if not all_products:
                return jsonify({
                    'success': False,
                    'error': f'Номенклатура для магазина {store_name} не найдена'
                }), 404
            
            # Сохраняем результаты мониторинга
            today = date.today()
            record_check_results(store_id, all_products, set(checked_items), today)
            
            # Создаем ТОЛЬКО СТРОГО ЗАЩИЩЕННЫЙ профессиональный отчет
            report_filename = create_protected_report_for_period(today, today)
            
            if report_filename and os.path.exists(report_filename):
                logger.info(f"✅ СТРОГО ЗАЩИЩЕННЫЙ Excel отчет создан: {report_filename}")
                
                return jsonify({
                    'success': True,
                    'message': f'Профессиональный отчет создан: {os.path.basename(report_filename)}',
                    'report_file': report_filename
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось создать Excel отчет'
                }), 500
                
        except Exception as db_error:
            logger.error(f"Ошибка создания отчета: {db_error}")
            return jsonify({
                'success': False,
                'error': f'Ошибка создания отчета: {str(db_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Ошибка в create_professional_excel_report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-file')
def download_file():
    """API для скачивания файла по полному пути"""
    try:
        file_path = request.args.get('file')
        
        if not file_path:
            return jsonify({'error': 'Не указан путь к файлу'}), 400
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Файл не найден'}), 404
        
        # Разделяем путь на директорию и имя файла
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        logger.info(f"Скачивание файла: {filename} из {directory}")
        return send_from_directory(directory, filename, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Ошибка скачивания файла: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regions')
def regions():
    """API для получения списка регионов"""
    try:
        regions_data = get_all_regions()
        
        return jsonify({
            'success': True,
            'regions': [
                {
                    'id': region[0],
                    'name': region[1],
                    'networks_count': len(get_networks_by_region(region[0])),
                    'stores_count': sum(len(get_stores_by_network(net[0])) 
                                      for net in get_networks_by_region(region[0]))
                }
                for region in regions_data
            ]
        })
    except Exception as e:
        logger.error(f"Ошибка в regions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks/<int:region_id>')
def networks(region_id):
    """API для получения сетей по региону"""
    try:
        networks_data = get_networks_by_region(region_id)
        
        return jsonify({
            'success': True,
            'networks': [
                {
                    'id': network[0],
                    'name': network[1],
                    'stores_count': len(get_stores_by_network(network[0]))
                }
                for network in networks_data
            ]
        })
    except Exception as e:
        logger.error(f"Ошибка в networks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stores/<int:network_id>')
def stores(network_id):
    """API для получения магазинов по сети с адресами из Excel"""
    try:
        stores_data = get_stores_by_network(network_id)
        checked_stores = get_checked_stores_for_date(date.today())
        
        # Получаем адреса из Excel файлов
        store_addresses = get_store_addresses_from_excel()
        
        stores_list = []
        for store in stores_data:
            store_id = store[0]
            store_number = store[1]
            
            # Ищем адрес в Excel данных
            address = store_addresses.get(store_id, store[2] if len(store) > 2 else 'Адрес не найден')
            
            stores_list.append({
                'id': store_id,
                'number': store_number,
                'name': f"№{store_number}",
                'address': address,
                'status': 'checked' if store_id in checked_stores else 'pending'
            })
        
        return jsonify({
            'success': True,
            'stores': stores_list
        })
    except Exception as e:
        logger.error(f"Ошибка в stores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search-stores/<int:network_id>')
def search_stores(network_id):
    """API для поиска магазинов по номеру или адресу"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': True,
                'stores': []
            })
        
        # Используем функцию поиска из database.py
        try:
            from database_demo import find_stores_in_network
        except ImportError:
            from database import find_stores_in_network
        stores_data = find_stores_in_network(network_id, query)
        checked_stores = get_checked_stores_for_date(date.today())
        
        # Получаем адреса из Excel файлов
        store_addresses = get_store_addresses_from_excel()
        
        stores_list = []
        for store in stores_data:
            store_id = store['id']
            store_number = store['number']
            
            # Ищем адрес в Excel данных
            address = store_addresses.get(store_id, store['address'] if store['address'] else 'Адрес не найден')
            
            stores_list.append({
                'id': store_id,
                'number': store_number,
                'name': f"№{store_number}",
                'address': address,
                'status': 'checked' if store_id in checked_stores else 'pending'
            })
        
        return jsonify({
            'success': True,
            'stores': stores_list
        })
    except Exception as e:
        logger.error(f"Ошибка в search_stores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nomenclature/<int:store_id>')
def nomenclature(store_id):
    """API для получения номенклатуры магазина"""
    try:
        try:
            from database_demo import get_nomenclature_by_store_id, get_checked_items_for_store_date
        except ImportError:
            from database import get_nomenclature_by_store_id, get_checked_items_for_store_date
        from datetime import date
        
        # Получаем номенклатуру для магазина
        nomenclature_data = get_nomenclature_by_store_id(store_id)
        # Исправляем: get_nomenclature_by_store_id возвращает sqlite3.Row объекты
        items = [item[0] for item in nomenclature_data]  # item[0] это product_name
        
        # Получаем уже отмеченные товары за сегодня
        today = date.today()
        checked_items = get_checked_items_for_store_date(store_id, today)
        
        return jsonify({
            'success': True,
            'items': items,
            'checked': list(checked_items)
        })
    except Exception as e:
        logger.error(f"Ошибка в nomenclature: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка загрузки номенклатуры: {str(e)}'
        }), 500

@app.route('/api/today-report')
def today_report():
    """API для получения отчета за сегодня"""
    try:
        today = date.today()
        checked_stores = get_checked_stores_for_date(today)
        
        if not checked_stores:
            return jsonify({
                'success': True,
                'date': today.strftime('%d.%m.%Y'),
                'stores_count': 0,
                'message': 'За сегодня еще не было проверок'
            })
        
        # Получаем детальную информацию о проверенных магазинах
        try:
            from database_demo import cursor, monitoring_checks, DEMO_STORES, DEMO_NETWORKS
            # В демо режиме создаем данные из памяти
            stores_info = []
            date_str = today.isoformat()
            
            for store_id in checked_stores:
                # Находим информацию о магазине
                store_data = next((s for s in DEMO_STORES if s[0] == store_id), None)
                if not store_data:
                    continue
                    
                # Находим сеть
                network_data = next((n for n in DEMO_NETWORKS if n[0] == store_data[3]), None)
                network_name = network_data[1] if network_data else "Неизвестная сеть"
                
                # Получаем данные проверки
                store_checks = monitoring_checks.get(store_id, {})
                date_checks = store_checks.get(date_str, {})
                
                total_checks = len(date_checks)
                present_items = sum(1 for is_present in date_checks.values() if is_present)
                
                stores_info.append({
                    'id': store_id,
                    'number': store_data[1],
                    'address': store_data[2],
                    'network_name': network_name,
                    'total_checks': total_checks,
                    'present_items': present_items,
                    'completion_rate': round((present_items / total_checks) * 100, 1) if total_checks > 0 else 0
                })
                
        except ImportError:
            from database import cursor
            
            cursor.execute("""
                SELECT s.id, s.number, s.address, n.name as network_name,
                       COUNT(mc.id) as total_checks,
                       SUM(CASE WHEN mc.is_present = 1 THEN 1 ELSE 0 END) as present_items
                FROM stores s
                JOIN networks n ON s.network_id = n.id
                JOIN monitoring_checks mc ON s.id = mc.store_id
                WHERE mc.check_date = ? AND s.id IN ({})
                GROUP BY s.id, s.number, s.address, n.name
                ORDER BY s.number
            """.format(','.join('?' * len(checked_stores))), 
            [today] + list(checked_stores))
            
            stores_data = cursor.fetchall()
            
            stores_info = []
            for store in stores_data:
                stores_info.append({
                    'id': store['id'],
                    'number': store['number'],
                    'address': store['address'],
                    'network_name': store['network_name'],
                    'total_checks': store['total_checks'],
                    'present_items': store['present_items'],
                    'completion_rate': round((store['present_items'] / store['total_checks']) * 100, 1) if store['total_checks'] > 0 else 0
                })
        
        return jsonify({
            'success': True,
            'date': today.strftime('%d.%m.%Y'),
            'stores_count': len(checked_stores),
            'stores': stores_info,
            'total_checks': sum(store['total_checks'] for store in stores_info),
            'total_present': sum(store['present_items'] for store in stores_info)
        })
        
    except Exception as e:
        logger.error(f"Ошибка в today_report: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка получения отчета: {str(e)}'
        }), 500

@app.route('/api/download-report')
def download_report():
    """API для скачивания Excel отчета"""
    try:
        store_id = request.args.get('store_id')
        report_date = request.args.get('date')
        
        if not store_id or not report_date:
            return jsonify({'error': 'Не указаны store_id или date'}), 400
        
        # Ищем последний созданный файл для этого магазина
        import glob
        import os
        
        logger.info(f"Ищем отчет для магазина {store_id} за дату {report_date}")
        
        # Ищем файлы отчетов по дате
        pattern = f"reports/Отчет_*{report_date}*.xlsx"
        files = glob.glob(pattern)
        
        logger.info(f"Найдено файлов по паттерну '{pattern}': {len(files)}")
        for f in files:
            logger.info(f"  - {f}")
        
        if files:
            # Берем самый новый файл
            latest_file = max(files, key=os.path.getctime)
            logger.info(f"Выбран файл: {latest_file}")
            
            if os.path.exists(latest_file):
                # Разделяем путь на директорию и имя файла
                directory = os.path.dirname(latest_file)
                filename = os.path.basename(latest_file)
                
                logger.info(f"Отправляем файл: {filename} из директории: {directory}")
                return send_from_directory(directory, filename, as_attachment=True)
            else:
                logger.error(f"Файл не существует: {latest_file}")
                return jsonify({'error': 'Файл отчета не найден'}), 404
        else:
            # Показываем все файлы в папке reports для отладки
            all_files = glob.glob("reports/*.xlsx")
            logger.info(f"Все файлы в reports/: {all_files}")
            return jsonify({'error': f'Отчет не найден. Паттерн: {pattern}'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка скачивания отчета: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-period-report', methods=['POST'])
def generate_period_report():
    """API для создания СТРОГО ЗАЩИЩЕННОГО отчета за период"""
    try:
        from report_protection import create_protected_report_for_period
        from database import get_checked_stores_for_date
        from datetime import datetime
        import os
        
        data = request.get_json()
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'error': 'Не указаны даты периода'
            }), 400
        
        # Парсим даты
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Неверный формат даты: {str(e)}'
            }), 400
        
        logger.info(f"🛡️ СТРОГО ЗАЩИЩЕННОЕ создание отчета за период с {start_date} по {end_date}")
        
        # Проверяем наличие данных за период
        from datetime import timedelta
        all_checked_stores = set()
        current_date = start_date
        while current_date <= end_date:
            checked_stores = get_checked_stores_for_date(current_date)
            all_checked_stores.update(checked_stores)
            current_date += timedelta(days=1)
        
        if not all_checked_stores:
            return jsonify({
                'success': False,
                'error': f'Нет данных за период с {start_date.strftime("%d.%m.%Y")} по {end_date.strftime("%d.%m.%Y")}'
            }), 404
        
        logger.info(f"Найдено {len(all_checked_stores)} проверенных магазинов за период")
        
        # Создаем ТОЛЬКО СТРОГО ЗАЩИЩЕННЫЙ профессиональный отчет
        report_path = create_protected_report_for_period(start_date, end_date)
        logger.info(f"✅ СТРОГО ЗАЩИЩЕННЫЙ отчет за период создан: {report_path}")
        
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            logger.info(f"Размер файла: {file_size} байт")
            
            if file_size == 0:
                logger.error("Создан пустой файл отчета")
                return jsonify({
                    'success': False,
                    'error': 'Создан пустой файл отчета'
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Отчет за период с {start_date.strftime("%d.%m.%Y")} по {end_date.strftime("%d.%m.%Y")}',
                'report_file': report_path,
                'stores_count': len(all_checked_stores)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Не удалось создать файл отчета'
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка в generate_period_report: {e}")
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/download-period-report')
def download_period_report():
    """API для скачивания Excel отчета за период"""
    try:
        from database import create_report_for_period
        from datetime import datetime
        import os
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Не указаны даты периода'}), 400
        
        # Парсим даты
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({'error': f'Неверный формат даты: {str(e)}'}), 400
        
        logger.info(f"Скачивание отчета за период с {start_date} по {end_date}")
        
        # Создаем отчет
        report_path = create_report_for_period(start_date, end_date)
        logger.info(f"Отчет создан: {report_path}")
        
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            logger.info(f"Размер файла: {file_size} байт")
            
            if file_size == 0:
                logger.error("Создан пустой файл отчета")
                return jsonify({'error': 'Создан пустой файл отчета'}), 500
            
            # Разделяем путь на директорию и имя файла
            directory = os.path.dirname(report_path)
            filename = os.path.basename(report_path)
            
            logger.info(f"Отправляем файл: {filename} из директории: {directory}")
            return send_from_directory(directory, filename, as_attachment=True)
        else:
            logger.error(f"Файл не существует: {report_path}")
            return jsonify({'error': 'Файл отчета не найден'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка скачивания отчета за период: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-today-report')
def download_today_report():
    """API для скачивания Excel отчета за сегодня"""
    try:
        from database import create_report_for_period
        from flask import Response
        import glob
        import os
        
        today = date.today()
        logger.info(f"Создание отчета за сегодня: {today}")
        
        # Проверяем наличие данных
        checked_stores = get_checked_stores_for_date(today)
        if not checked_stores:
            logger.warning("Нет данных за сегодня для создания отчета")
            return jsonify({'error': 'Нет данных за сегодня для создания отчета'}), 404
        
        logger.info(f"Найдено {len(checked_stores)} проверенных магазинов")
        
        # Создаем отчет
        report_path = create_report_for_period(today, today)
        logger.info(f"Отчет создан: {report_path}")
        
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            logger.info(f"Размер файла: {file_size} байт")
            
            if file_size == 0:
                logger.error("Создан пустой файл отчета")
                return jsonify({'error': 'Создан пустой файл отчета'}), 500
            
            # Читаем файл в память
            with open(report_path, 'rb') as f:
                file_data = f.read()
            
            # Создаем имя файла для скачивания (только латинские символы)
            download_filename = f"Report_today_{today.strftime('%Y-%m-%d')}.xlsx"
            
            logger.info(f"Отправляем файл: {download_filename}, размер: {len(file_data)} байт")
            
            # Создаем ответ с правильными заголовками
            response = Response(
                file_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={
                    'Content-Disposition': f'attachment; filename="{download_filename}"',
                    'Content-Length': str(len(file_data)),
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
            
            return response
        else:
            logger.error(f"Файл отчета не создан: {report_path}")
            return jsonify({'error': 'Не удалось создать файл отчета'}), 500
            
    except Exception as e:
        logger.error(f"Ошибка создания/скачивания отчета за сегодня: {e}")
        return jsonify({'error': f'Ошибка создания отчета: {str(e)}'}), 500

@app.route('/api/send-today-report', methods=['POST'])
def send_today_report():
    """API для отправки отчета за сегодня в Telegram"""
    try:
        from database import create_report_for_period
        import os
        
        today = date.today()
        logger.info(f"Отправка отчета за сегодня: {today}")
        
        # Проверяем наличие данных
        checked_stores = get_checked_stores_for_date(today)
        if not checked_stores:
            return jsonify({
                'success': False,
                'error': 'Нет данных за сегодня для отправки отчета'
            })
        
        # Создаем отчет
        report_path = create_report_for_period(today, today)
        logger.info(f"Отчет для отправки создан: {report_path}")
        
        if os.path.exists(report_path):
            # Здесь можно добавить логику отправки в Telegram
            # Пока просто возвращаем успех
            return jsonify({
                'success': True,
                'message': f'Отчет за {today.strftime("%d.%m.%Y")} готов к отправке',
                'file_path': report_path,
                'stores_count': len(checked_stores)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Не удалось создать файл отчета'
            })
            
    except Exception as e:
        logger.error(f"Ошибка отправки отчета за сегодня: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка отправки отчета: {str(e)}'
        })

@app.route('/health')
def health_check():
    """API для проверки состояния сервера"""
    try:
        from database import cursor
        
        # Проверяем подключение к БД
        cursor.execute("SELECT COUNT(*) as count FROM stores")
        stores_count = cursor.fetchone()['count']
        
        return jsonify({
            'status': 'healthy',
            'message': 'Сервер работает нормально',
            'database': 'connected',
            'stores_count': stores_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': f'Ошибка сервера: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/get-last-price', methods=['POST'])
def get_last_price_api():
    """API для получения последней цены товара в сети"""
    try:
        data = request.get_json()
        network_id = data.get('network_id')
        product_name = data.get('product_name')
        
        if not network_id or not product_name:
            return jsonify({
                'success': False,
                'error': 'Не указаны network_id или product_name'
            }), 400
        
        logger.info(f"Поиск последней цены для товара '{product_name}' в сети {network_id}")
        last_price = get_last_price_in_network(network_id, product_name)
        
        if last_price:
            logger.info(f"Найдена цена: {last_price['regular_price']} руб.")
            return jsonify({
                'success': True,
                'price_data': {
                    'regular_price': last_price['regular_price'],
                    'promo_price': last_price['promo_price'],
                    'has_promo': last_price['has_promo'],
                    'check_date': last_price['check_date'],
                    'store_number': last_price['store_number']
                }
            })
        else:
            logger.info(f"Цена не найдена для товара '{product_name}'")
            return jsonify({
                'success': True,
                'price_data': None
            })
    except Exception as e:
        logger.error(f"Ошибка получения последней цены: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save-price', methods=['POST'])
def save_price_api():
    """API для сохранения цены товара"""
    try:
        data = request.get_json()
        
        required_fields = ['store_id', 'product_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует обязательное поле: {field}'
                }), 400
        
        # Сохраняем цену и остатки
        result = save_price_check(
            store_id=data['store_id'],
            product_name=data['product_name'],
            check_date=date.today(),
            regular_price=data.get('regular_price'),
            promo_price=data.get('promo_price'),
            has_promo=data.get('has_promo', False),
            stock_quantity=data.get('stock_quantity')
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Цена и остатки сохранены успешно'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка сохранения цены'
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка сохранения цены: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-price', methods=['POST'])
def get_price_api():
    """API для получения цены товара за сегодня"""
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        product_name = data.get('product_name')
        
        if not store_id or not product_name:
            return jsonify({
                'success': False,
                'error': 'Не указаны store_id или product_name'
            }), 400
        
        price_data = get_price_check(store_id, product_name, date.today())
        if price_data:
            return jsonify({
                'success': True,
                'price_data': {
                    'regular_price': price_data['regular_price'],
                    'promo_price': price_data['promo_price'],
                    'has_promo': price_data['has_promo'],
                    'price_notes': price_data['price_notes']
                }
            })
        else:
            return jsonify({
                'success': True,
                'price_data': None
            })
    except Exception as e:
        logger.error(f"Ошибка получения цены: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Проверяем наличие базы данных
    if not os.path.exists('bot_database.db'):
        logger.error("База данных не найдена!")
        exit(1)
    
    logger.info("Запуск Web App сервера...")
    logger.info("Web App будет доступен по адресу: http://localhost:5000")
    
    # Запускаем сервер
    app.run(
        host='0.0.0.0',  # Слушаем на всех интерфейсах
        port=5000,       # Порт 5000
        debug=False,     # Отключаем debug для стабильности
        threaded=True    # Включаем многопоточность
    )