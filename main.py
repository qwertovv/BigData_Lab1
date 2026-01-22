import requests
import os
import json
import urllib.parse
import time
import hashlib
import cv2

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
    def download_image(self, url, save_path):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except:
            return False
    
    def generate_filename(self, index):
        return f"{index:04d}.jpg"
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
    def download_class_images(self, class_name, query_in_russian):
        folder_path = self.class_folders[class_name]
        image_urls = self.get_yandex_image_urls(query_in_russian)
        
        downloaded_count = 0
        for i, url in enumerate(image_urls):
            if downloaded_count >= 1000:
                break
                
            filename = self.generate_filename(downloaded_count)
            save_path = os.path.join(folder_path, filename)
            
            if self.download_image(url, save_path):
                downloaded_count += 1
        
        return downloaded_count
    def remove_duplicates(self, folder_path):
        image_hashes = set()
        files_to_remove = []
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.jpg'):
                filepath = os.path.join(folder_path, filename)
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if file_hash in image_hashes:
                    files_to_remove.append(filepath)
                else:
                    image_hashes.add(file_hash)
        
        for filepath in files_to_remove:
            os.remove(filepath)
        
        return len(files_to_remove)
    def preview_images(self, class_name):
        folder_path = self.class_folders[class_name]
        image_files = os.listdir(folder_path)[:10]
        
        for filename in image_files:
            filepath = os.path.join(folder_path, filename)
            image = cv2.imread(filepath)
            if image is not None:
                print(f"{filename}: Размер {image.shape}")

if __name__ == "__main__":
    downloader = ImageDownloader()
    downloader.create_class_folders()
    print("Папки созданы")