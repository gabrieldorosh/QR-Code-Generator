from flask import Flask, request, render_template_string
import io, base64
from encoding import generate_codewords
from matrix import place_data_bits, initialise_matrix
from masking import apply_mask, calculate_penalty
from main import get_format_info_bits
from PIL import Image, ImageDraw

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>QR Code Generator</title>
    <style>
        body { max-width: 600px; margin: 40px auto; }
        .warning { background-color: #ffdddd; border-left: 6px solid #f44336; padding: 10px; margin-bottom: 20px; }
        form { margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 10px; }
        label { margin-top: 10px; display: block; }
        button { padding: 10px 20px; font-size: 16px; }
        img { border: 1px solid #ddd; }
        .error { color: red; margin-top: 10px; }
        .slideshow img { max-width: 100%; margin-bottom: 10px;}
    </style>
</head>
<body>
    <h1>QR Code Generator</h1>
    <div class="warning">
        <strong>Warning:</strong> Malicious QR codes can redirect to phishing or malware sites. Only scan codes from trusted sources.
    </div>
    <form method="post" action="/generate">
        <label for="text">Enter text to encode:</label>
        <input type="text" id="text" name="text" required placeholder="Enter your message">
        <label for="foreground_colour">Foreground Colour:</label>
        <input type="colour" id="foreground_colour" name="foreground_colour" value="#000000">
        <label for="background_colour">Background Colour:</label>
        <input type="colour" id="background_colour" name="background_colour" value="#ffffff">
        <label for="shape">Module Shape:</label>
        <select id="shape" name="shape">
            <option value="square">Square</option>
            <option value="circle">Circle</option>
        </select>
        <label for="pixel_size">Pixel Size:</label>
        <input type="number" id="pixel_size" name="pixel_size" value="10" min="1" max="100">
        <label><input type="checkbox" name="slideshow">Show step by step slideshow</label> 
        <button type="submit">Generate QR Code</button>
    </form>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    {% if slideshow_images %}
    <h2>Step by Step Slideshow:</h2>
    <div class="slideshow">
        {% for img in slideshow_images %}
            <img src="data:image/png;base64,{{ img }}" alt="Step {{ loop.index }}">
        {% endfor %}
    </div>
    {% endif %}
    {% if qr_img %}
    <h2>Generated QR Code:</h2>
    <img src="data:image/png;base64,{{ qr_img }}" alt="QR Code">
    {% endif %}
</body>
</html>
"""

def matrix_to_png_bytes(matrix, pixel_size=10, border=4, foreground_color=(0, 0, 0), background_color=(255, 255, 255), shape='square'):
    size = len(matrix)
    img_size = (size + 2*border) * pixel_size
    img = Image.new("RGB", (img_size, img_size), background_color)
    draw = ImageDraw.Draw(img)
    pixels = img.load()
    for r in range(size):
        for c in range(size):
            if matrix[r][c] is None:
                continue
            fill = foreground_color if matrix[r][c] == 1 else background_color
            x0 = (c + border) * pixel_size
            y0 = (r + border) * pixel_size
            x1 = x0 + pixel_size
            y1 = y0 + pixel_size
            if shape == 'circle':
                draw.ellipse([x0, y0, x1, y1], fill=fill)
            else:  # square
                draw.rectangle([x0, y0, x1, y1], fill=fill)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)

    return bio


@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.get('text', '')
    foreground = request.form.get('foreground_colour', '#000000')
    background = request.form.get('background_colour', '#ffffff')
    shape = request.form.get('shape', 'square')
    pixel_size = int(request.form.get('pixel_size', 10))
    slideshow = 'slideshow' in request.form

    # Version 1-L capacity is 19 bytes
    try:
        raw = data.encode('iso-8859-1', 'strict')
    except UnicodeEncodeError:
        return render_template_string(INDEX_HTML, qr_img=None, error="Unsupported character in input.")
    
    # auto detect version based on input length
    if len(raw) <= 19:
        version = 1
    elif len(raw) <= 34:
        version = 2
    else:
        return render_template_string(INDEX_HTML, qr_img=None, error="Input too long (max 34 bytes for version 2).")
    
    # generate codewords
    data_cw, ecc_cw = generate_codewords(data, version)
    data_bits = ''.join(format(b, '08b') for b in data_cw)
    ecc_bits = ''.join(format(b, '08b') for b in ecc_cw)

    # build initial matrix and record steps
    matrix, reserved = initialise_matrix(version)
    steps = []
    if slideshow:
        # step 1: just patterns
        img1 = matrix_to_png_bytes(matrix, pixel_size, 4, tuple(int(foreground.lstrip('#')[i:i+2],16) for i in (0,2,4)), tuple(int(background.lstrip('#')[i:i+2],16) for i in (0,2,4)), shape)
        steps.append(base64.b64encode(img1.getvalue()).decode('ascii'))

    # step 2: place data bits
    place_data_bits(matrix, reserved, data_bits + ecc_bits)
    if slideshow:
        img2 = matrix_to_png_bytes(matrix, pixel_size, 4, tuple(int(foreground.lstrip('#')[i:i+2],16) for i in (0,2,4)), tuple(int(background.lstrip('#')[i:i+2],16) for i in (0,2,4)), shape)
        steps.append(base64.b64encode(img2.getvalue()).decode('ascii'))

    # step 3: choose best mask
    best_mask, best_matrix, _ = min(
        ((mask, apply_mask(matrix, reserved, mask), calculate_penalty(apply_mask(matrix, reserved, mask)))
         for mask in range(8)), key=lambda x: x[2]
    )
    if slideshow:
        img3 = matrix_to_png_bytes(best_matrix, pixel_size, 4, tuple(int(foreground.lstrip('#')[i:i+2],16) for i in (0,2,4)), tuple(int(background.lstrip('#')[i:i+2],16) for i in (0,2,4)), shape)
        steps.append(base64.b64encode(img3.getvalue()).decode('ascii'))

    # step 4: place format info bits
    format_bits = get_format_info_bits('L', best_mask)
    fmt_positions = [(8, i) for i in range(6)] + [(8,7), (8,8), (7,8)] + [(i,8) for i in range(5, -1, -1)]
    for idx, (r, c) in enumerate(fmt_positions):
        best_matrix[r][c] = int(format_bits[idx])
    if slideshow:
        img4 = matrix_to_png_bytes(best_matrix, pixel_size, 4, tuple(int(foreground.lstrip('#')[i:i+2],16) for i in (0,2,4)), tuple(int(background.lstrip('#')[i:i+2],16) for i in (0,2,4)), shape)
        steps.append(base64.b64encode(img4.getvalue()).decode('ascii'))

    # second copy of format info (bottom-left & top-right)
    size = len(best_matrix)
    sec_fmt_positions = (
        [(size-1 - i, 8) for i in range(7)]
        + [(8, size-8)]
        + [(8, size-7 + i) for i in range(7)]
    )
    for idx, (r, c) in enumerate(sec_fmt_positions):
        best_matrix[r][c] = int(format_bits[idx])

    # render image
    img_bytes = matrix_to_png_bytes(best_matrix, pixel_size, 4, tuple(int(foreground.lstrip('#')[i:i+2],16) for i in (0,2,4)), tuple(int(background.lstrip('#')[i:i+2],16) for i in (0,2,4)), shape)
    qr_img = base64.b64encode(img_bytes.getvalue()).decode('ascii')

    return render_template_string(INDEX_HTML, qr_img=qr_img, slideshow_images=steps if slideshow else None)

if __name__ == '__main__':
    app.run(debug=True)