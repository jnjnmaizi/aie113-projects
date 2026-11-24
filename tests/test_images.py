from io import BytesIO
import pytest
from PIL import Image
from bean_vision.adapters.images import decode_image, InvalidImage, ImageTooLarge


@pytest.mark.parametrize("mode", ["RGB", "L", "RGBA"])
def test_rgb_conversion(mode):
    stream = BytesIO()
    Image.new(mode, (8, 8)).save(stream, format="PNG")
    assert decode_image(stream.getvalue()).mode == "RGB"


def test_pixel_limit(photo):
    with pytest.raises(ImageTooLarge):
        decode_image(photo, 100)


@pytest.mark.parametrize("data", [b"", b"not an image", b"\x89PNG\r\n\x1a\n"])
def test_invalid_image(data):
    with pytest.raises(InvalidImage):
        decode_image(data)


def test_gif_rejected():
    stream = BytesIO()
    Image.new("RGB", (8, 8)).save(stream, format="GIF")
    with pytest.raises(InvalidImage):
        decode_image(stream.getvalue())
