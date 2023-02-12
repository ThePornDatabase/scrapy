from io import BytesIO
from typing import Any

import pytesseract

from PIL import Image, ImageFilter, ImageOps
from unidecode import unidecode


class BaseOCR:
    def get_data_from_image(self, image: bytes) -> Any:
        image = self._get_image_from_bytes(image)
        image = self._image_pre_processing(image)
        text: str = pytesseract.image_to_string(image)
        res = self._text_post_processing(text)

        return res

    @staticmethod
    def _image_pre_processing(image: Image.Image) -> Image.Image:
        image = ImageOps.expand(image, 20)
        image = image.convert('L')
        image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

        return image

    @staticmethod
    def _text_post_processing(text: str) -> str:
        text = unidecode(text)
        text = text.strip()

        return text

    @staticmethod
    def _get_image_from_bytes(data: bytes):
        data = BytesIO(data)
        return Image.open(data)
