import base64

from app.services.export_utils import json_value


def test_json_value_base64_encodes_raw_bytes_losslessly():
    original = b"\x00\x01fake-audio-bytes\xff"

    encoded = json_value(original)

    assert isinstance(encoded, str)
    assert base64.b64decode(encoded) == original
