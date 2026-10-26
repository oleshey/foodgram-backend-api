import csv
import os

from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из файла ingredients.csv в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к CSV-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            raise CommandError(f'Файл {file_path} не найден')

        ingredients_to_create = []

        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                ingredients_to_create = self._parse_csv_data(csv_reader)

        except FileNotFoundError as file_not_found_error:
            error_message = str(file_not_found_error)
            raise CommandError(f'Файл не найден: {error_message}')

        except PermissionError as permission_error:
            error_message = str(permission_error)
            raise CommandError(f'Нет прав на чтение файла: {error_message}')

        except csv.Error as csv_parsing_error:
            error_message = str(csv_parsing_error)
            raise CommandError(f'Ошибка парсинга CSV-файла: {error_message}')

        except UnicodeDecodeError as encoding_error:
            error_message = str(encoding_error)
            raise CommandError(f'Ошибка кодировки файла: {error_message}')

        except Exception as unexpected_error:
            error_message = str(unexpected_error)
            raise CommandError(
                f'Неожиданная ошибка при обработке файла: {error_message}'
            )

        if ingredients_to_create:
            try:
                created_count = Ingredient.objects.bulk_create(
                    ingredients_to_create,
                    ignore_conflicts=True
                )
                rows_count = len(created_count)
                success_message = (
                    f'Ингредиенты успешно загружены (строк: {rows_count})'
                )
                self.stdout.write(self.style.SUCCESS(success_message))

            except Exception as database_error:
                error_message = str(database_error)
                raise CommandError(
                    f'Ошибка при сохранении в базу данных: {error_message}'
                )

        else:
            self.stdout.write(
                self.style.WARNING('Нет новых ингредиентов для загрузки')
            )

    def _parse_csv_data(self, csv_reader):
        """Парсит данные из CSV-ридера."""
        ingredients = []

        for row in csv_reader:
            if not row or len(row) < 2:
                continue

            if (
                row[0].lower() == 'name'
                and row[1].lower() == 'measurement_unit'
            ):
                continue

            ingredient_name = row[0].strip()
            measurement_unit = row[1].strip()

            if not ingredient_name or not measurement_unit:
                continue

            ingredients.append(
                Ingredient(
                    name=ingredient_name,
                    measurement_unit=measurement_unit
                )
            )

        return ingredients
