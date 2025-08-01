#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск веб-приложения
"""

from app import app
import os

if __name__ == '__main__':
    # Для разработки
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print("🌐 Запуск веб-приложения...")
    print(f"📱 Адрес: http://localhost:{port}")
    print(f"🔧 Debug режим: {debug_mode}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )