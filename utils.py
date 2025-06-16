import base64
import hashlib

import cv2
from PIL import Image
from PIL.Image import Resampling
from pyzbar.pyzbar import decode


def convert_image_to_base64(image):
    _, buffer = cv2.imencode(".jpg", image)
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return base64_str


def get_QR(image):
    qr_codes = decode(image)
    if qr_codes:
        return qr_codes[0].data.decode("utf-8")
    return None


def resize_image(image: Image.Image, scale_factor: float) -> Image.Image:
    width, height = image.size
    new_size = (int(width * scale_factor), int(height * scale_factor))
    resized_image = image.resize(
        new_size, Resampling.LANCZOS
    )  # <— используем Resampling
    return resized_image


def hash_string(data: str, algorithm: str = "sha256") -> str:
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode("utf-8"))
    return hash_obj.hexdigest()
