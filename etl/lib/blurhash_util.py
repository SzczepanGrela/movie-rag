import io

import blurhash

X_COMPONENTS = 4
Y_COMPONENTS = 3


def encode_blurhash(jpeg_bytes: bytes) -> str:
    return str(blurhash.encode(io.BytesIO(jpeg_bytes), X_COMPONENTS, Y_COMPONENTS))
