import os
import requests
import time
import cv2
import hashlib
import json
import urllib.parse

class ImageDownloader:
    def __init__(self):
        # Создаем основную папку dataset если ее нет
        self.dataset_path = "dataset"
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)
            print(f"Создана папка: {self.dataset_path}")
        
        # Заголовки для запросов (имитируем браузер)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Папки для каждого класса
        self.classes = ['tiger', 'leopard']
        self.class_folders = {}
        
    def create_class_folders(self):
        """Создание папок для каждого класса"""
        for class_name in self.classes:
            class_path = os.path.join(self.dataset_path, class_name)
            if not os.path.exists(class_path):
                os.makedirs(class_path)
                print(f"Создана папка для класса: {class_name}")
            self.class_folders[class_name] = class_path
    
    def get_yandex_image_urls(self, query, num_images=1200):
        """
        Получение URL изображений через Яндекс.Картинки
        Используем API Яндекс.Картинок
        """
        image_urls = []
        page = 0  # Начинаем с первой страницы
        
        try:
            # Преобразуем запрос в URL-формат
            encoded_query = urllib.parse.quote(query)
            
            while len(image_urls) < num_images:
                # Формируем URL для API Яндекс.Картинок
                # Здесь используется эмпирически найденный формат запроса
                url = f"https://yandex.ru/images/api/v2/search"
                
                params = {
                    'text': query,
                    'type': 'photo',
                    'p': page,  # номер страницы
                    'nomisspell': 1,
                    'noreask': 1,
                    'isize': 'large',  # запрашиваем большие изображения
                }
                
                print(f"Запрос страницы {page} для: {query}")
                
                # Отправляем GET-запрос
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"Ошибка {response.status_code} при запросе")
                    break
                
                try:
                    # Пробуем распарсить JSON ответ
                    data = response.json()
                    
                    # Проверяем структуру ответа
                    if 'items' not in data or not data['items']:
                        print("Больше нет изображений")
                        break
                    
                    # Извлекаем URL изображений
                    for item in data['items']:
                        if len(image_urls) >= num_images:
                            break
                        
                        # Пробуем разные пути к URL изображения
                        img_url = None
                        
                        # Проверяем возможные структуры данных
                        if 'img_href' in item:
                            img_url = item['img_href']
                        elif 'origin' in item and 'url' in item['origin']:
                            img_url = item['origin']['url']
                        elif 'url' in item:
                            img_url = item['url']
                        elif 'preview' in item and 'url' in item['preview']:
                            # Иногда нужно получить оригинал через preview
                            img_url = item['preview']['url']
                            # Пробуем преобразовать в оригинальный URL
                            img_url = img_url.replace('m00', 'orig00')
                        
                        if img_url and img_url.startswith('http'):
                            # Проверяем, что это действительно изображение
                            if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                if img_url not in image_urls:  # Проверяем уникальность
                                    image_urls.append(img_url)
                                    print(f"Найдено изображений: {len(image_urls)}/{num_images}")
                    
                    page += 1
                    
                    # Задержка чтобы не перегружать сервер
                    time.sleep(1)
                    
                except json.JSONDecodeError:
                    print("Ошибка парсинга JSON")
                    # Попробуем парсить HTML если JSON не получился
                    self.parse_html_for_images(response.text, image_urls, num_images)
                    break
                    
        except Exception as e:
            print(f"Ошибка при получении URL: {e}")
        
        return image_urls[:num_images]
    
    def parse_html_for_images(self, html, image_urls, num_images):
        """Резервный метод: парсинг HTML если API не работает"""
        try:
            # Ищем все ссылки на изображения в HTML
            import re
            # Паттерн для поиска URL изображений
            img_patterns = [
                r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                r'data-src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                r'orig="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
            ]
            
            for pattern in img_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if len(image_urls) >= num_images:
                        return
                    if match not in image_urls:
                        image_urls.append(match)
                        print(f"Найдено изображений в HTML: {len(image_urls)}/{num_images}")
        except Exception as e:
            print(f"Ошибка при парсинге HTML: {e}")
    
    def download_image(self, url, save_path):
        """Загрузка одного изображения"""
        try:
            # Добавляем реферер для Яндекс
            headers = self.headers.copy()
            headers['Referer'] = 'https://yandex.ru/images/'
            
            # Устанавливаем таймауты
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            
            if response.status_code == 200:
                # Проверяем, что это изображение
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    print(f"Не изображение: {content_type}")
                    return False
                
                # Сохраняем изображение
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Проверяем, что файл не пустой
                if os.path.getsize(save_path) > 1024:  # Минимум 1KB
                    # Конвертируем в JPG если нужно
                    self.convert_to_jpg(save_path)
                    return True
                else:
                    os.remove(save_path)  # Удаляем пустой файл
                    return False
                    
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")
            return False
    
    def convert_to_jpg(self, image_path):
        """Конвертация изображения в JPG если нужно"""
        try:
            # Читаем изображение
            img = cv2.imread(image_path)
            if img is not None:
                # Если успешно прочитано, сохраняем как JPG
                if not image_path.lower().endswith('.jpg'):
                    new_path = os.path.splitext(image_path)[0] + '.jpg'
                    cv2.imwrite(new_path, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    # Удаляем старый файл
                    if new_path != image_path:
                        os.remove(image_path)
            else:
                # Если не удалось прочитать, удаляем файл
                os.remove(image_path)
        except Exception as e:
            print(f"Ошибка конвертации {image_path}: {e}")
    
    def generate_filename(self, index):
        """Генерация имени файла с ведущими нулями"""
        return f"{index:04d}.jpg"
    
    def remove_duplicates(self, folder_path):
        """Удаление дубликатов изображений по хешу"""
        print(f"Проверка дубликатов в {folder_path}...")
        image_hashes = set()
        files_to_remove = []
        
        # Сначала собираем все JPG файлы
        jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
        
        for filename in jpg_files:
            filepath = os.path.join(folder_path, filename)
            try:
                # Вычисляем хеш содержимого файла
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if file_hash in image_hashes:
                    files_to_remove.append(filepath)
                else:
                    image_hashes.add(file_hash)
            except Exception as e:
                print(f"Ошибка обработки {filename}: {e}")
                continue
        
        # Удаляем дубликаты
        for filepath in files_to_remove:
            os.remove(filepath)
            print(f"Удален дубликат: {os.path.basename(filepath)}")
        
        return len(files_to_remove)
    
    def download_class_images(self, class_name, query_in_russian):
        """Загрузка изображений для одного класса"""
        print(f"\n{'='*50}")
        print(f"Начинаем загрузку изображений для класса: {class_name}")
        print(f"Запрос на русском: {query_in_russian}")
        print('='*50)
        
        folder_path = self.class_folders[class_name]
        
        # Ищем изображения через API
        print("Поиск URL изображений через API Яндекс...")
        image_urls = self.get_yandex_image_urls(query_in_russian, num_images=1200)
        print(f"Найдено URL изображений: {len(image_urls)}")
        
        if len(image_urls) == 0:
            print("Не удалось найти изображения. Попробуем альтернативный метод...")
            # Альтернативный метод: прямой поиск через HTML
            encoded_query = urllib.parse.quote(query_in_russian)
            search_url = f"https://yandex.ru/images/search?text={encoded_query}&isize=large"
            
            response = requests.get(search_url, headers=self.headers)
            if response.status_code == 200:
                self.parse_html_for_images(response.text, image_urls, 1200)
        
        # Загружаем изображения
        downloaded_count = 0
        failed_count = 0
        
        for i, url in enumerate(image_urls):
            if downloaded_count >= 1000:
                break
                
            filename = self.generate_filename(downloaded_count)
            save_path = os.path.join(folder_path, filename)
            
            print(f"[{class_name}] Загрузка {downloaded_count+1}/1000...")
            
            if self.download_image(url, save_path):
                downloaded_count += 1
            else:
                failed_count += 1
            
            # Небольшая задержка чтобы не перегружать сервер
            time.sleep(0.5)
        
        print(f"\nЗагрузка завершена для класса {class_name}:")
        print(f"  Успешно: {downloaded_count}")
        print(f"  Ошибок: {failed_count}")
        
        # Удаляем дубликаты
        removed = self.remove_duplicates(folder_path)
        print(f"  Удалено дубликатов: {removed}")
        
        # Переименовываем файлы чтобы не было пропусков
        self.renumber_files(folder_path)
        
        return downloaded_count
    
    def renumber_files(self, folder_path):
        """Перенумерация файлов после удаления дубликатов"""
        # Сортируем файлы по имени
        jpg_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')])
        
        # Временная папка для избежания конфликтов имен
        temp_folder = os.path.join(folder_path, "temp")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        
        # Перемещаем файлы во временную папку с новыми именами
        for i, filename in enumerate(jpg_files):
            old_path = os.path.join(folder_path, filename)
            new_filename = self.generate_filename(i)
            temp_path = os.path.join(temp_folder, new_filename)
            
            os.rename(old_path, temp_path)
        
        # Перемещаем обратно
        for filename in os.listdir(temp_folder):
            old_path = os.path.join(temp_folder, filename)
            new_path = os.path.join(folder_path, filename)
            os.rename(old_path, new_path)
        
        # Удаляем временную папку
        os.rmdir(temp_folder)
    
    def preview_images(self, class_name, num_to_preview=10):
        """Просмотр части изображений для проверки"""
        print(f"\nПросмотр изображений класса: {class_name}")
        folder_path = self.class_folders[class_name]
        
        # Получаем список JPG файлов
        image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')])[:num_to_preview]
        
        if not image_files:
            print("  Нет изображений для просмотра")
            return
        
        for filename in image_files:
            filepath = os.path.join(folder_path, filename)
            try:
                # Читаем изображение
                image = cv2.imread(filepath)
                if image is not None:
                    print(f"  {filename}: Размер {image.shape}")
                    
                    # Показываем изображение (раскомментируйте для просмотра)
                    # cv2.imshow(f"{class_name} - {filename}", image)
                    # cv2.waitKey(500)  # Показываем 500 мс
                    # cv2.destroyAllWindows()
                else:
                    print(f"  {filename}: Не удалось прочитать (битый файл)")
                    # Удаляем битый файл
                    os.remove(filepath)
            except Exception as e:
                print(f"  {filename}: Ошибка {e}")
    
    def check_and_fill_dataset(self):
        """Проверка и дополнение набора данных если нужно"""
        print("\nПроверка набора данных...")
        
        for class_name in self.classes:
            folder_path = self.class_folders[class_name]
            jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
            current_count = len(jpg_files)
            
            print(f"  {class_name}: {current_count} изображений")
            
            if current_count < 1000:
                print(f"  Необходимо добавить еще {1000 - current_count} изображений")
                # Дополнительные запросы для дозагрузки
                additional_queries = {
                    'tiger': ['тигр амурский', 'тигр бенгальский', 'тигр фото'],
                    'leopard': ['леопард снежный', 'леопард африканский', 'леопард животное фото']
                }
                
                for additional_query in additional_queries.get(class_name, []):
                    if current_count >= 1000:
                        break
                        
                    print(f"  Дополнительный запрос: {additional_query}")
                    self.download_class_images(class_name, additional_query)
                    
                    # Обновляем счетчик
                    jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
                    current_count = len(jpg_files)
    
    def run(self):
        """Основной метод выполнения"""
        print("Начало выполнения задания")
        print("="*60)
        
        # 1. Создаем папки
        self.create_class_folders()
        
        # 2. Загружаем изображения для каждого класса
        class_queries = {
            'tiger': 'тигр',
            'leopard': 'леопард'
        }
        
        for class_name in self.classes:
            # Загружаем изображения
            count = self.download_class_images(class_name, class_queries[class_name])
            
            # Просматриваем часть изображений для проверки
            self.preview_images(class_name)
        
        # 3. Проверяем и дополняем если нужно
        self.check_and_fill_dataset()
        
        print("\n" + "="*60)
        print("Задание выполнено!")
        print(f"Итоговые данные сохранены в папке: {self.dataset_path}")
        
        # Выводим статистику
        print("\nИтоговая статистика:")
        for class_name in self.classes:
            folder_path = self.class_folders[class_name]
            num_files = len([f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')])
            print(f"  {class_name}: {num_files} изображений")

# Запуск программы
if __name__ == "__main__":
    downloader = ImageDownloader()
    downloader.run()