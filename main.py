import requests
import os

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