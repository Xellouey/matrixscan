// Service Worker для PWA
const CACHE_NAME = 'monitoring-app-v1';
const urlsToCache = [
    '/',
    '/manifest.json',
    '/icon-192.png',
    '/icon-512.png'
];

// Установка Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker: Установка');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Кэширование файлов');
                return cache.addAll(urlsToCache);
            })
            .catch(err => {
                console.log('Service Worker: Ошибка кэширования', err);
            })
    );
});

// Активация Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker: Активация');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Удаление старого кэша', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Перехват запросов
self.addEventListener('fetch', event => {
    // Только для GET запросов
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Возвращаем кэшированную версию или загружаем из сети
                if (response) {
                    console.log('Service Worker: Загрузка из кэша', event.request.url);
                    return response;
                }

                console.log('Service Worker: Загрузка из сети', event.request.url);
                return fetch(event.request).then(response => {
                    // Проверяем валидность ответа
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // Клонируем ответ для кэширования
                    const responseToCache = response.clone();

                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseToCache);
                        });

                    return response;
                });
            })
            .catch(() => {
                // Показываем офлайн страницу для HTML запросов
                if (event.request.destination === 'document') {
                    return caches.match('/');
                }
            })
    );
});

// Обработка push уведомлений (если понадобится)
self.addEventListener('push', event => {
    console.log('Service Worker: Push уведомление получено');

    const options = {
        body: event.data ? event.data.text() : 'Новое уведомление',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Открыть приложение',
                icon: '/icon-192.png'
            },
            {
                action: 'close',
                title: 'Закрыть',
                icon: '/icon-192.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Система мониторинга', options)
    );
});

// Обработка клика по уведомлению
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Клик по уведомлению');

    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});