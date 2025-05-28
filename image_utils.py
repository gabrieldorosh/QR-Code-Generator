from PIL import Image

# save the QR matrix as a png
def save_matrix_as_image(matrix: list[list[int]], filename: str, pixel_size: int = 10, border: int = 4):
    size = len(matrix)
    img_size = (size + 2*border) * pixel_size
    img = Image.new("RGB", (img_size, img_size), "white")
    pixels = img.load()

    for r in range(size):
        for c in range(size):
            color = (0, 0, 0) if matrix[r][c] == 1 else (255, 255, 255)
            for dy in range(pixel_size):
                for dx in range(pixel_size):
                    x = (c + border) * pixel_size + dx
                    y = (r + border) * pixel_size + dy
                    pixels[x, y] = color

    # save and display the image
    img.save(filename)
    img.show()