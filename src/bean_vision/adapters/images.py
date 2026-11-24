from io import BytesIO
import warnings
from PIL import Image, UnidentifiedImageError


class InvalidImage(ValueError):
    pass


class ImageTooLarge(ValueError):
    pass


def decode_image(data: bytes, max_pixels: int = 16_000_000) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG"}:
                    raise InvalidImage("Only JPEG and PNG images are supported")
                if source.width * source.height > max_pixels:
                    raise ImageTooLarge("Image dimensions exceed the limit")
                source.verify()
            with Image.open(BytesIO(data)) as source:
                # Match the notebook exactly: RGB, no extra crop or EXIF rotation.
                return source.convert("RGB")
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ImageTooLarge("Image dimensions exceed the limit") from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        if isinstance(exc, (InvalidImage, ImageTooLarge)):
            raise
        raise InvalidImage("File must be a valid JPEG or PNG image") from exc
