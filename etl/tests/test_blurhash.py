import io

from PIL import Image

from lib.blurhash_util import encode_blurhash


def _sample_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 48), (120, 80, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def test_encode_blurhash_returns_nonempty_string() -> None:
    result = encode_blurhash(_sample_jpeg())
    assert isinstance(result, str)
    assert len(result) > 6
