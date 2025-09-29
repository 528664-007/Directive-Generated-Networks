import torch
import os
import zipfile
import io
from flask import Flask, render_template, request, send_file
from model import VAE
from PIL import Image
import numpy as np

app = Flask(__name__)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = VAE(latent_dim=20).to(device)
model.load_state_dict(torch.load('vae_model.pth', weights_only=True))
model.eval()

# Ensure static/generated exists
os.makedirs('static/generated', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    images = []
    num_samples = 10
    seed = None
    if request.method == 'POST':
        if 'generate' in request.form:
            num_samples = int(request.form.get('num_samples', 10))
            num_samples = max(1, min(num_samples, 20))
            seed_str = request.form.get('seed', '')
            seed = int(seed_str) if seed_str.isdigit() else None
            if seed is not None:
                torch.manual_seed(seed)
            # Generate samples
            with torch.no_grad():
                z = torch.randn(num_samples, 20).to(device)
                samples = model.decode(z).cpu().numpy()
            
            # Clear old images
            for f in os.listdir('static/generated'):
                os.remove(os.path.join('static/generated', f))
            
            for i in range(num_samples):
                img_array = samples[i].reshape(28, 28) * 255
                img = Image.fromarray(img_array.astype('uint8'), 'L')
                img_path = f'static/generated/generated_{i}.png'
                img.save(img_path)
                images.append(f'generated/generated_{i}.png')
        elif 'clear' in request.form:
            for f in os.listdir('static/generated'):
                os.remove(os.path.join('static/generated', f))
    
    return render_template('index.html', images=images, num_samples=num_samples, seed=seed)

@app.route('/interpolate', methods=['POST'])
def interpolate():
    alpha = float(request.form.get('alpha', 0.5))
    seed_a = int(request.form.get('seed_a', 0))
    seed_b = int(request.form.get('seed_b', 1))
    
    with torch.no_grad():
        torch.manual_seed(seed_a)
        z_a = torch.randn(1, 20).to(device)
        torch.manual_seed(seed_b)
        z_b = torch.randn(1, 20).to(device)
        z_interp = z_a * (1 - alpha) + z_b * alpha
        sample = model.decode(z_interp).cpu().numpy()[0]
    
    img_array = sample.reshape(28, 28) * 255
    img = Image.fromarray(img_array.astype('uint8'), 'L')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return send_file(img_bytes, mimetype='image/png')

@app.route('/download')
def download():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for f in os.listdir('static/generated'):
            zf.write(os.path.join('static/generated', f), f)
    memory_file.seek(0)
    return send_file(memory_file, download_name='generated_images.zip', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
