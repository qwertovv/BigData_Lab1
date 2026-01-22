import requests
import os
import json
import urllib.parse
import time

class ImageDownloader:
    def __init__(self):
        self.dataset_path = "dataset"
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)
        
        self.classes = ['tiger', 'leopard']
        self.class_folders = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    def get_yandex_image_urls(self, query, num_images=1200):
        image_urls = []
        page = 0
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://yandex.ru/images/api/v2/search"
            
            params = {
                'text': query,
                'type': 'photo',
                'p': page,
                'isize': 'large',
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        if 'origin' in item and 'url' in item['origin']:
                            img_url = item['origin']['url']
                            image_urls.append(img_url)
        
        except Exception as e:
            print(f"Ошибка: {e}")
        
        return image_urls
    def create_class_folders(self):
        for class_name in self.classes:
            class_path = os.path.join(self.dataset_path, class_name)
            if not os.path.exists(class_path):
                os.makedirs(class_path)
            self.class_folders[class_name] = class_path

if __name__ == "__main__":
    downloader = ImageDownloader()
    downloader.create_class_folders()
    print("Папки созданы")