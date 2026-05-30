# gif_maker.py
import io
from PIL import Image

def make_gif(image_bytes_list, duration=1.0):
    frames = [Image.open(io.BytesIO(img)).convert("RGBA") for img in image_bytes_list]
    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=int(duration * 1000),
        loop=0,
        disposal=2
    )
    return output.getvalue()
