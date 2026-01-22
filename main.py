import os
import requests
import time
import hashlib
import re
import urllib.parse
from PIL import Image

class ImageDownloader:
    def __init__(self):
        # Создаем основную папку dataset если ее нет
        self.dataset_path = "dataset"
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)
            print(f"Создана папка: {self.dataset_path}")
        
        # Заголовки для запросов (имитируем браузер)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
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
    
    def get_image_urls_simple(self, query, num_images=50):
        """
        Простой парсинг HTML страницы Яндекс.Картинок
        """
        image_urls = []
        page = 0
        
        try:
            # Кодируем запрос
            encoded_query = urllib.parse.quote(query)
            
            while len(image_urls) < num_images:
                # Формируем URL для поиска
                if page == 0:
                    url = f"https://yandex.ru/images/search?text={encoded_query}&isize=large"
                else:
                    url = f"https://yandex.ru/images/search?p={page}&text={encoded_query}&isize=large"
                
                print(f"Запрос страницы {page}: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"Ошибка {response.status_code}")
                    break
                
                html = response.text
                
                # Ищем URL изображений в HTML
                # Паттерны для поиска URL изображений в Яндекс.Картинках
                patterns = [
                    r'"origin":{"url":"([^"]+)"',  # JSON форма
                    r'src="(https://[^"]+\.ya[_\-]?img\.ru/[^"]+)"',  # Прямые ссылки
                    r'img_url=([^&]+)&',  # Параметры URL
                    r'https://avatars\.mds\.yandex\.net/[^"\s]+',  # Аватары
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        if len(image_urls) >= num_images:
                            break
                        
                        # Очищаем URL
                        if match.startswith('https://'):
                            img_url = match
                        elif match.startswith('//'):
                            img_url = 'https:' + match
                        else:
                            # Декодируем URL если он в кодированном виде
                            try:
                                img_url = urllib.parse.unquote(match)
                                if not img_url.startswith('http'):
                                    continue
                            except:
                                continue
                        
                        # Проверяем, что это изображение
                        if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']):
                            if img_url not in image_urls:
                                image_urls.append(img_url)
                                print(f"Найдено изображений: {len(image_urls)}/{num_images}")
                
                # Если на этой странице не нашли изображений, пробуем другой метод
                if len(image_urls) == 0:
                    # Альтернативный метод поиска
                    img_tags = re.findall(r'<img[^>]+src="([^">]+)"', html)
                    for img_src in img_tags:
                        if len(image_urls) >= num_images:
                            break
                        
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        
                        if img_src.startswith('http') and any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                            if img_src not in image_urls:
                                image_urls.append(img_src)
                                print(f"Найдено (alt метод): {len(image_urls)}/{num_images}")
                
                page += 1
                
                # Задержка между запросами
                time.sleep(2)
                
                # Ограничим количество страниц
                if page > 5:  # Максимум 5 страниц
                    break
                    
        except Exception as e:
            print(f"Ошибка при получении URL: {e}")
        
        return image_urls[:num_images]
    
    def get_image_urls_alternative(self, query, num_images=50):
        """
        Альтернативный метод - используем Bing/Google Images API
        """
        image_urls = []
        
        try:
            # Используем Bing Image Search API (бесплатно, до 1000 запросов в месяц)
            # Для теста используем открытые API
            subscription_key = ""  # Оставьте пустым, будем использовать другой метод
            
            if not subscription_key:
                # Если нет ключа API, используем простой веб-скрапинг Google Images
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers)
                html = response.text
                
                # Ищем изображения в Google
                # Google хранит изображения в base64 или в данных-аттрибутах
                import base64
                
                # Ищем URL в JSON данных
                pattern = r'"ou":"([^"]+)"'
                matches = re.findall(pattern, html)
                
                for match in matches:
                    if len(image_urls) >= num_images:
                        break
                    
                    if match.startswith('http') and any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png']):
                        if match not in image_urls:
                            image_urls.append(match)
                            print(f"Найдено (Google): {len(image_urls)}/{num_images}")
                
        except Exception as e:
            print(f"Ошибка альтернативного метода: {e}")
        
        return image_urls[:num_images]
    
    def download_image(self, url, save_path):
        """Загрузка одного изображения"""
        try:
            # Добавляем реферер
            headers = self.headers.copy()
            headers['Referer'] = 'https://yandex.ru/'
            
            # Пробуем загрузить с таймаутом
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            
            if response.status_code == 200:
                # Проверяем content-type
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type and 'octet-stream' not in content_type:
                    print(f"Не изображение: {content_type}")
                    return False
                
                # Сохраняем файл
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Проверяем размер файла
                if os.path.getsize(save_path) > 1024:  # Минимум 1KB
                    # Пробуем открыть как изображение для проверки
                    try:
                        with Image.open(save_path) as img:
                            img.verify()  # Проверяем, что это валидное изображение
                        return True
                    except:
                        # Если не удалось открыть, удаляем файл
                        os.remove(save_path)
                        return False
                else:
                    os.remove(save_path)
                    return False
                    
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False
    
    def convert_to_jpg(self, image_path):
        """Конвертация изображения в JPG"""
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Создаем новое имя файла
                base_name = os.path.splitext(image_path)[0]
                new_path = base_name + '.jpg'
                
                # Сохраняем как JPG
                img.save(new_path, 'JPEG', quality=90)
                
                # Удаляем старый файл если нужно
                if new_path != image_path:
                    os.remove(image_path)
                    
        except Exception as e:
            print(f"Ошибка конвертации: {e}")
    
    def generate_filename(self, index):
        """Генерация имени файла с ведущими нулями"""
        return f"{index:04d}.jpg"
    
    def download_test_images(self):
        """Загрузка тестовых изображений из открытых источников"""
        print("Загрузка тестовых изображений из открытых источников...")
        
        # URL тестовых изображений тигра
        tiger_urls = [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Walking_tiger_female.jpg/800px-Walking_tiger_female.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Tiger_in_the_water.jpg/800px-Tiger_in_the_water.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/2012_Suedchinesischer_Tiger.JPG/800px-2012_Suedchinesischer_Tiger.JPG",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Bengal_tiger_%28Panthera_tigris_tigris%29_female_3_crop.jpg/800px-Bengal_tiger_%28Panthera_tigris_tigris%29_female_3_crop.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/White_tiger_sitting.jpg/800px-White_tiger_sitting.jpg",
        ]
        
        # URL тестовых изображений леопарда
        leopard_urls = [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Leopard_standing_in_tree_2.jpg/800px-Leopard_standing_in_tree_2.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Leopard_in_the_Colchester_Zoo.jpg/800px-Leopard_in_the_Colchester_Zoo.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Leopard_africa.jpg/800px-Leopard_africa.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Leopard_in_South_Africa.jpg/800px-Leopard_in_South_Africa.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Snow_leopard_1.jpg/800px-Snow_leopard_1.jpg",
        ]
        
        # Загружаем изображения тигра
        tiger_folder = self.class_folders['tiger']
        for i, url in enumerate(tiger_urls):
            filename = self.generate_filename(i)
            save_path = os.path.join(tiger_folder, filename)
            
            print(f"Загрузка тигра {i+1}/{len(tiger_urls)}...")
            if self.download_image(url, save_path):
                self.convert_to_jpg(save_path)
        
        # Загружаем изображения леопарда
        leopard_folder = self.class_folders['leopard']
        for i, url in enumerate(leopard_urls):
            filename = self.generate_filename(i)
            save_path = os.path.join(leopard_folder, filename)
            
            print(f"Загрузка леопарда {i+1}/{len(leopard_urls)}...")
            if self.download_image(url, save_path):
                self.convert_to_jpg(save_path)
    
    def run_simple_test(self):
        """Простой тест - загрузка нескольких изображений"""
        print("="*60)
        print("ПРОСТОЙ ТЕСТ: Загрузка 5 изображений для каждого класса")
        print("="*60)
        
        # Создаем папки
        self.create_class_folders()
        
        # Загружаем тестовые изображения
        self.download_test_images()
        
        # Проверяем результаты
        print("\nПроверка результатов:")
        for class_name in self.classes:
            folder = self.class_folders[class_name]
            files = [f for f in os.listdir(folder) if f.lower().endswith('.jpg')]
            print(f"  {class_name}: {len(files)} изображений")
            
            # Показываем информацию о файлах
            for file in files[:3]:  # Первые 3 файла
                filepath = os.path.join(folder, file)
                size = os.path.getsize(filepath)
                print(f"    {file}: {size} байт")

def main():
    """Основная функция"""
    print("Проверка зависимостей...")
    
    try:
        # Проверяем Pillow
        from PIL import Image
        print("✓ Pillow установлен")
    except ImportError:
        print("✗ Pillow не установлен. Установите: pip install Pillow")
        return
    
    try:
        # Проверяем requests
        import requests
        print("✓ requests установлен")
        
        # Проверяем подключение к интернету
        test_response = requests.get("https://www.google.com", timeout=5)
        if test_response.status_code == 200:
            print("✓ Подключение к интернету есть")
        else:
            print("✗ Проблемы с подключением к интернету")
            return
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return
    
    # Запускаем тест
    downloader = ImageDownloader()
    downloader.run_simple_test()
    
    print("\n" + "="*60)
    print("Хотите попробовать загрузить больше изображений с Яндекс? (y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        print("\nПопытка загрузки с Яндекс.Картинок...")
        
        # Пробуем загрузить с Яндекса
        for class_name in downloader.classes:
            folder = downloader.class_folders[class_name]
            query = "тигр" if class_name == "tiger" else "леопард"
            
            print(f"\nПоиск изображений для '{class_name}' (запрос: '{query}')...")
            
            # Получаем URL
            urls = downloader.get_image_urls_simple(query, num_images=10)
            print(f"Найдено URL: {len(urls)}")
            
            # Загружаем изображения
            existing_files = len([f for f in os.listdir(folder) if f.lower().endswith('.jpg')])
            
            for i, url in enumerate(urls):
                if i >= 5:  # Ограничимся 5 изображениями для теста
                    break
                    
                filename = downloader.generate_filename(existing_files + i)
                save_path = os.path.join(folder, filename)
                
                print(f"  Загрузка {i+1}/5...")
                if downloader.download_image(url, save_path):
                    downloader.convert_to_jpg(save_path)
                time.sleep(1)  # Задержка между загрузками
            
            # Обновляем счетчик файлов
            files = [f for f in os.listdir(folder) if f.lower().endswith('.jpg')]
            print(f"  Всего изображений {class_name}: {len(files)}")

if __name__ == "__main__":
    main()