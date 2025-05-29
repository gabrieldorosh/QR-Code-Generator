from flask import Flask, request, render_template_string
import io, base64
from encoding import generate_codewords
from matrix import create_full_matrix
from masking import apply_mask, calculate_penalty
from main import get_format_info_bits
from PIL import Image

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
    button { padding: 10px 20px; font-size: 16px; }
    img { border: 1px solid #ddd; }
    .error { color: red; margin-top: 10px; }
  </style>
</head>
<body>
  <h1>QR Code Generator</h1>
  <div class="warning">
    <strong>Warning:</strong> Malicious QR codes can redirect to phishing or malware sites. Only scan codes from trusted sources.
  </div>
  <form method="post" action="/generate">
    <label for="text">Enter text to encode (max 19 characters):</label>
    <input type="text" id="text" name="text" required maxlength="19" placeholder="Enter up to 19 bytes">
    <button type="submit">Generate QR Code</button>
  </form>
  {% if error %}
  <div class="error">{{ error }}</div>
  {% endif %}
  {% if qr_img %}
  <h2>Generated QR Code:</h2>
  <img src="data:image/png;base64,{{ qr_img }}" alt="QR Code">
  {% endif %}
</body>
</html>
"""

def matrix_to_png_bytes(matrix, pixel_size=10, border=4):
    size = len(matrix)
    img_size = (size + 2*border) * pixel_size
    img = Image.new("RGB", (img_size, img_size), "white")
    pixels = img.load()
    for r in range(size):
        for c in range(size):
            color = (0,0,0) if matrix[r][c] == 1 else (255,255,255)
            for dy in range(pixel_size):
                for dx in range(pixel_size):
                    x = (c + border) * pixel_size + dx
                    y = (r + border) * pixel_size + dy
                    pixels[x, y] = color
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
    # Version 1-L capacity is 19 bytes
    try:
        data.encode('iso-8859-1', 'strict')
    except UnicodeEncodeError:
        return render_template_string(INDEX_HTML, qr_img=None, error="Unsupported character in input.")
    if len(data.encode('iso-8859-1', 'strict')) > 19:
        return render_template_string(INDEX_HTML, qr_img=None, error="Input too long (max 19 bytes).")
    version = 1
    # generate codewords
    data_cw, ecc_cw = generate_codewords(data, version)
    data_bits = ''.join(format(b, '08b') for b in data_cw)
    ecc_bits = ''.join(format(b, '08b') for b in ecc_cw)
    base_matrix, reserved = create_full_matrix(version, data_bits, ecc_bits)
    # choose best mask
    best = min(
        ((mask, apply_mask(base_matrix, reserved, mask), calculate_penalty(apply_mask(base_matrix, reserved, mask)))
         for mask in range(8)),
        key=lambda x: x[2]
    )
    best_mask, best_matrix, _ = best
    # place format info bits
    format_bits = get_format_info_bits('L', best_mask)
    fmt_positions = [(8, i) for i in range(6)] + [(8,7), (8,8), (7,8)] + [(i,8) for i in range(5, -1, -1)]
    for idx, (r, c) in enumerate(fmt_positions):
        best_matrix[r][c] = int(format_bits[idx])
    # render image
    img_bytes = matrix_to_png_bytes(best_matrix)
    encoded = base64.b64encode(img_bytes.getvalue()).decode('ascii')
    return render_template_string(INDEX_HTML, qr_img=encoded)

if __name__ == '__main__':
    app.run(debug=True)