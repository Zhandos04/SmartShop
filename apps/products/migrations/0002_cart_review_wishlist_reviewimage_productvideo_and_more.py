# Generated by Django 4.2.5 on 2025-05-06 14:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0001_initial_products'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Корзина',
                'verbose_name_plural': 'Корзины',
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='Рейтинг')),
                ('text', models.TextField(verbose_name='Текст отзыва')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'unique_together': {('product', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('products', models.ManyToManyField(related_name='wishlists', to='products.product')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Список желаний',
                'verbose_name_plural': 'Списки желаний',
            },
        ),
        migrations.CreateModel(
            name='ReviewImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='reviews/', verbose_name='Изображение')),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.review')),
            ],
            options={
                'verbose_name': 'Изображение отзыва',
                'verbose_name_plural': 'Изображения отзывов',
            },
        ),
        migrations.CreateModel(
            name='ProductVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', models.FileField(upload_to='products/videos/', verbose_name='Видео')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='products.product')),
            ],
            options={
                'verbose_name': 'Видео товара',
                'verbose_name_plural': 'Видео товаров',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/', verbose_name='Изображение')),
                ('is_main', models.BooleanField(default=False, verbose_name='Основное изображение')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.product')),
            ],
            options={
                'verbose_name': 'Изображение товара',
                'verbose_name_plural': 'Изображения товаров',
            },
        ),
        migrations.CreateModel(
            name='ProductTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track_price', models.BooleanField(default=True, verbose_name='Отслеживать цену')),
                ('track_stock', models.BooleanField(default=True, verbose_name='Отслеживать наличие')),
                ('track_discount', models.BooleanField(default=True, verbose_name='Отслеживать скидки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracking_users', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracked_products', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Отслеживание товара',
                'verbose_name_plural': 'Отслеживания товаров',
                'unique_together': {('user', 'product')},
            },
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('value', models.CharField(max_length=255, verbose_name='Значение')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='products.product')),
            ],
            options={
                'verbose_name': 'Атрибут товара',
                'verbose_name_plural': 'Атрибуты товаров',
                'unique_together': {('product', 'name')},
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='products.cart')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'verbose_name': 'Элемент корзины',
                'verbose_name_plural': 'Элементы корзины',
                'unique_together': {('cart', 'product')},
            },
        ),
    ]
