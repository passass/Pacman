from sys import exit as exitsys

try:
    from PIL import Image
except Exception:
    print('для работы этого инструмента, обязана быть установлена библеотека Pillow')
    exitsys()
import csv

im = Image.open(f'data/pictures_points/{input("что открыть? (файл должен находиться в папке data/pictures_points)")}')
pixels = im.load()  # список с пикселями
x, y = im.size  # ширина (x) и высота (y) изображения
#im1 = Image.new('RGB', (x, y), (0, 255, 0))
#pixels1 = im1.load()
with open(f'data/{input("куда сохранять? (написать только имя файла, а сохраняется в папке data)")}.csv',
          'w+', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            #pixels1[i, j] = r, g, b
            if r == 255 and g == 238:
                writer.writerow([i, j])
                print(f'{i}, {j} является помеченной')
    #im1.save('data/pictures_points/kia.png')