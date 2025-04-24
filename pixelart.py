from PIL import Image

def pixelate_image(input_path, output_path, pixel_in_row, dominant_coefficient=0.5, color_threshold=10):
    """
    Перетворює зображення на піксель-арт із зсувом рядків.

    Args:
        input_path (str): Шлях до вхідного зображення.
        output_path (str): Шлях для збереження вихідного зображення.
        pixel_in_row (int): Кількість пікселів у рядку.
        dominant_coefficient (float): Коефіцієнт підсилення домінуючого кольору (0-1)
        color_threshold (int): Поріг відмінності кольорів для об'єднання (0-255)
    """
    try:
        img = Image.open(input_path)
        width, height = img.size
        pixel_size = width // pixel_in_row

        new_width = width // pixel_size
        new_height = height // pixel_size

        # Створюємо зображення з додатковим простором для сітки
        grid_size = 1  # Розмір сітки в пікселях
        new_img = Image.new('RGB', (new_width * (pixel_size + grid_size), new_height * (pixel_size + grid_size)), (255, 255, 255))

        print(f"Processing pixel block: {width}, {height}, {new_width}, {new_width}")

        for i in range(new_height):
            for j in range(new_width):
                left = j * pixel_size
                upper = i * pixel_size
                right = left + pixel_size
                lower = upper + pixel_size
                print(f"Processing pixel block: {i}, {j}, {left}, {upper}, {right}, {lower}")
                
                # Зсув рядків
                shift = pixel_size // 2 if i % 2 != 0 else 0
                
                box = (left, upper, right, lower)
                region = img.crop(box)
                color = get_average_color(region, dominant_coefficient, color_threshold)
                
                # Враховуємо сітку та зсув при вставці кольору
                paste_box = (
                    j * (pixel_size + grid_size) + shift,
                    i * (pixel_size + grid_size),
                    j * (pixel_size + grid_size) + pixel_size + shift,
                    i * (pixel_size + grid_size) + pixel_size
                )
                new_img.paste(color, paste_box)

        new_img.save(output_path)
        print(f"Successfully saved pixelated image to {output_path}")
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found")
    except Exception as e:
        print(f"Error processing image: {str(e)}")

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

# Використання
input_path = "pare.jpg"  # Замініть на шлях до вашого зображення
output_path = 'pxfox.png'  # Замініть на шлях для збереження вихідного зображення
pixel_in_row = 25  # Кількість пікселів у рядку
dominant_coefficient = 0.8  # Коефіцієнт підсилення домінуючого кольору
color_threshold = 20  # Поріг відмінності кольорів для об'єднання

pixelate_image(input_path, output_path, pixel_in_row, dominant_coefficient, color_threshold)