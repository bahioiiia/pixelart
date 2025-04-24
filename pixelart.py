from PIL import Image, ImageDraw
import math
import numpy as np
from sklearn.cluster import KMeans

def get_average_color(image, dominant_coefficient=0.5, color_threshold=10):
    """
    Обчислює середній колір зображення, ігноруючи фон та підсилюючи домінуючий колір.
    
    Args:
        image: Зображення для обробки
        dominant_coefficient (float): Коефіцієнт підсилення домінуючого кольору (0-1)
        color_threshold (int): Поріг відмінності кольорів для об'єднання (0-255)
    """
    pixels = list(image.getdata())
    background_color = pixels[0]  # Колір фону з лівого верхнього кута
    
    # Фільтруємо пікселі, ігноруючи фон
    filtered_pixels = [p for p in pixels if p != background_color]
    
    if not filtered_pixels:  # Якщо всі пікселі - фон
        return background_color
    
    # Групуємо схожі кольори
    color_groups = []
    for pixel in filtered_pixels:
        found_group = False
        for group in color_groups:
            # Перевіряємо чи колір належить до групи
            if all(abs(p - g) <= color_threshold for p, g in zip(pixel, group[0])):
                group.append(pixel)
                found_group = True
                break
        if not found_group:
            color_groups.append([pixel])
    
    # Знаходимо найбільшу групу кольорів
    largest_group = max(color_groups, key=len)
    
    # Обчислюємо середній колір з найбільшої групи
    r, g, b = 0, 0, 0
    count = len(largest_group)
    
    for pr, pg, pb in largest_group:
        r += pr
        g += pg
        b += pb
    
    avg_color = (r // count, g // count, b // count)
    
    # Знаходимо домінуючий колір (середній колір найбільшої групи)
    dominant_color = avg_color
    
    # Змішуємо середній колір з домінуючим згідно коефіцієнта
    mixed_color = tuple(
        int(avg * (1 - dominant_coefficient) + dom * dominant_coefficient)
        for avg, dom in zip(avg_color, dominant_color)
    )
    
    return mixed_color

def create_circle_mask(size):
    """Створює маску для кола заданого розміру."""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    
    # Радіус кола - половина розміру
    radius = size // 2
    # Координати центру
    center = (size // 2, size // 2)
    
    # Малюємо коло
    draw.ellipse(
        (center[0] - radius, center[1] - radius,
         center[0] + radius, center[1] + radius),
        fill=255
    )
    return mask

def sample_colors(image, pixel_in_row, dominant_coefficient=0.5, color_threshold=10):
    """
    Зчитує кольори з зображення та зберігає їх у масиві.
    
    Args:
        image: Вхідне зображення
        pixel_in_row (int): Кількість пікселів у рядку
        dominant_coefficient (float): Коефіцієнт підсилення домінуючого кольору (0-1)
        color_threshold (int): Поріг відмінності кольорів для об'єднання (0-255)
        
    Returns:
        list: Двовимірний масив кольорів
    """
    width, height = image.size
    input_pixel_size = width // pixel_in_row
    
    # Розрахунок кількості зразків
    samples_per_row = width // input_pixel_size
    num_rows = height // int(input_pixel_size * 0.866)
    
    # Ініціалізація масиву кольорів
    colors = []
    
    for i in range(num_rows):
        row_colors = []
        for j in range(samples_per_row):
            # Координати для зчитування кольору
            left = j * input_pixel_size
            upper = i * int(input_pixel_size * 0.866)
            right = left + input_pixel_size
            lower = upper + int(input_pixel_size * 0.866)
            
            box = (left, upper, right, lower)
            region = image.crop(box)
            color = get_average_color(region, dominant_coefficient, color_threshold)
            row_colors.append(color)
        
        colors.append(row_colors)
    
    return colors

def reduce_colors(colors, num_colors):
    """
    Зменшує кількість унікальних кольорів у масиві, об'єднуючи схожі кольори.
    
    Args:
        colors (list): Двовимірний масив кольорів
        num_colors (int): Бажана кількість унікальних кольорів
        
    Returns:
        list: Масив кольорів зі зменшеною кількістю унікальних кольорів
    """
    # Збираємо всі унікальні кольори
    unique_colors = set()
    for row in colors:
        unique_colors.update(row)
    
    # Якщо кількість унікальних кольорів менша за бажану, повертаємо оригінал
    if len(unique_colors) <= num_colors:
        return colors
    
    # Перетворюємо кольори в масив для кластеризації
    color_array = np.array(list(unique_colors))
    
    # Виконуємо k-means кластеризацію
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(color_array)
    
    # Створюємо словник для заміни кольорів
    color_map = {tuple(color): tuple(kmeans.cluster_centers_[kmeans.predict([color])[0]].astype(int))
                for color in unique_colors}
    
    # Застосовуємо заміну кольорів
    reduced_colors = []
    for row in colors:
        reduced_row = [color_map[tuple(color)] for color in row]
        reduced_colors.append(reduced_row)
    
    return reduced_colors

def generate_circle_image(colors, output_path):
    """
    Генерує зображення з кіл на основі масиву кольорів.
    
    Args:
        colors (list): Двовимірний масив кольорів
        output_path (str): Шлях для збереження вихідного зображення
    """
    # Фіксовані розміри сітки
    grid_horizontal = 46  # Відстань між центрами по горизонталі
    grid_vertical = 40    # Відстань між рядами
    circle_radius = 22    # Радіус кола
    
    # Розрахунок розмірів вихідного зображення
    output_width = len(colors[0]) * grid_horizontal + grid_horizontal // 2
    output_height = len(colors) * grid_vertical + grid_vertical
    output_img = Image.new('RGB', (output_width, output_height), (255, 255, 255))
    
    # Створюємо маску кола
    circle_mask = create_circle_mask(circle_radius * 2)
    
    # Генеруємо зображення
    for y in range(len(colors)):
        for x in range(len(colors[y])):
            # Зсув для чергування рядів
            x_offset = grid_horizontal // 2 if y % 2 != 0 else 0
            
            # Координати центру кола
            center_x = x * grid_horizontal + x_offset + circle_radius
            center_y = y * grid_vertical + circle_radius
            
            # Координати для вставки кола (з урахуванням радіуса)
            paste_x = center_x - circle_radius
            paste_y = center_y - circle_radius
            
            # Створюємо тимчасове зображення з кольором
            temp_img = Image.new('RGB', (circle_radius * 2, circle_radius * 2), colors[y][x])
            # Застосовуємо маску кола
            output_img.paste(temp_img, (paste_x, paste_y), circle_mask)
    
    output_img.save(output_path)
    print(f"Successfully saved circular pixelated image to {output_path}")

def pixelate_image(input_path, output_path, pixel_in_row, dominant_coefficient=0.5, color_threshold=10, num_colors=None):
    """
    Перетворює зображення на піксель-арт у формі кіл з фіксованою сіткою.

    Args:
        input_path (str): Шлях до вхідного зображення.
        output_path (str): Шлях для збереження вихідного зображення.
        pixel_in_row (int): Кількість пікселів у рядку.
        dominant_coefficient (float): Коефіцієнт підсилення домінуючого кольору (0-1)
        color_threshold (int): Поріг відмінності кольорів для об'єднання (0-255)
        num_colors (int): Кількість унікальних кольорів у вихідному зображенні
    """
    try:
        # Відкриваємо зображення
        img = Image.open(input_path)
        
        # Зчитуємо кольори
        print("Sampling colors from image...")
        colors = sample_colors(img, pixel_in_row, dominant_coefficient, color_threshold)
        
        # Зменшуємо кількість кольорів, якщо вказано
        if num_colors is not None:
            print(f"Reducing colors to {num_colors} unique colors...")
            colors = reduce_colors(colors, num_colors)
        
        # Генеруємо вихідне зображення
        print("Generating output image...")
        generate_circle_image(colors, output_path)
        
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found")
    except Exception as e:
        print(f"Error processing image: {str(e)}")

# Використання
input_path = "sol.jpg"  # Замініть на шлях до вашого зображення
output_path = 'pxcapybara.png'  # Замініть на шлях для збереження вихідного зображення
pixel_in_row = 50  # Кількість пікселів у рядку
dominant_coefficient = 0.9  # Коефіцієнт підсилення домінуючого кольору
color_threshold = 100  # Поріг відмінності кольорів для об'єднання
num_colors = 12  # Кількість унікальних кольорів у вихідному зображенні

pixelate_image(input_path, output_path, pixel_in_row, dominant_coefficient, color_threshold, num_colors)