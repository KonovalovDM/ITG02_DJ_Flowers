# core/management/commands/load_images.py
from django.core.management.base import BaseCommand
from django.core.files import File
from core.models import Product  # Убедитесь, что импортируете правильную модель
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Загружает изображения из папки media/products'

    def handle(self, *args, **kwargs):
        products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        for image_filename in os.listdir(products_dir):
            if image_filename.endswith('.jpg'):
                image_path = os.path.join(products_dir, image_filename)
                with open(image_path, 'rb') as image_file:
                    product = Product(
                        name=image_filename,
                        price=100.00
                    )
                    product.image.save(image_filename, File(image_file))
                    product.save()
        self.stdout.write(self.style.SUCCESS('Изображения успешно загружены'))

