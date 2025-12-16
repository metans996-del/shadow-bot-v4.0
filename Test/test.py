import base64
import os

# 1. Ваш полный путь к файлу
image_path = r"C:\Users\Zxc\v1-cyberpunk-tarot-ai\public\tarot-cards\XV - The Devil (Дьявол).webp"

# 2. Определяем MIME-тип (важно для Base64 URI)
mime_type = "image/webp"

# Проверка существования файла
if not os.path.exists(image_path):
    print(f"Ошибка: Файл не найден по пути: {image_path}")
else:
    try:
        with open(image_path, "rb") as image_file:
            # Кодируем содержимое файла в Base64
            base64_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Формируем полную строку с URI Data Scheme
        full_base64_url = f"data:{mime_type};base64,{base64_data}" 

        print("--- СГЕНЕРИРОВАННАЯ СТРОКА BASE64 ---")
        print("Скопируйте СТРОКУ НИЖЕ полностью и используйте ее в test_payload.json или в PowerShell:")
        # Печатаем строку, чтобы ее можно было скопировать
        print(full_base64_url) 
        print("-------------------------------------")

    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")