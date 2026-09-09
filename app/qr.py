"""Offline QR-image decoding and LIMITED EMV-style payload inspection.
No bank connection, payment execution, recipient authentication or full KHQR validation.
"""
import io
import warnings
from binascii import crc_hqx

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_PIXELS = 6_000_000

def decode_image(data: bytes) -> str:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image must be a PNG/JPEG no larger than 2 MiB.')
    from PIL import Image, UnidentifiedImageError
    import cv2
    import numpy as np
    # Only decode raster PNG/JPEG; do not accept SVG, PDF, GIF, ZIP or remote URLs.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as original:
                if original.format not in {'PNG', 'JPEG'}:
                    raise ValueError('Only PNG/JPEG images are supported.')
                if original.width * original.height > MAX_PIXELS:
                    raise ValueError('Resize the image to at most 6 megapixels.')
                original.load()
                image = original.convert('RGB')  # Metadata is not propagated or stored.
                image.thumbnail((1600,1600))
        pixels = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        cv2.setNumThreads(1)
        text, _, _ = cv2.QRCodeDetector().detectAndDecode(pixels)
        if not text:
            raise ValueError('No readable QR was found. Crop it more closely or paste the QR text. Screenshot text extraction is not implemented.')
        if len(text) > 6000:
            raise ValueError('Decoded QR text is too long.')
        return text
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('Invalid or oversized image.') from exc

def inspect_emv(payload: str) -> dict:
    """Strict subset, ASCII only. Report unsupported text instead of false validation.

    TLV lengths and the CRC provide structural/integrity checks, NOT authenticity.
    An attacker can generate a valid CRC. Full NBC SDK validation is a release gate.
    """
    disclaimer = 'A valid structure/checksum does not verify a recipient, account ownership, or a transaction. Confirm inside your bank app.'
    result = {'supported': True, 'structural_check_passed': False, 'crc_valid': False,
              'recipient_verified': False, 'notice': disclaimer}
    if not payload.isascii():
        result.update(supported=False, error='Non-ASCII payment QR requires the official KHQR SDK; not supported by this starter.')
        return result
    values, pos, crc_start = {}, 0, None
    try:
        while pos < len(payload):
            if pos + 4 > len(payload) or not payload[pos:pos+4].isdigit():
                raise ValueError('Malformed TLV header.')
            tag, length = payload[pos:pos+2], int(payload[pos+2:pos+4])
            end = pos + 4 + length
            if end > len(payload) or tag in values:
                raise ValueError('Invalid length or duplicate tag.')
            values[tag] = payload[pos+4:end]
            if tag == '63':
                if length != 4 or end != len(payload):
                    raise ValueError('Checksum must be the last four-character field.')
                crc_start = pos
            pos = end
        if values.get('00') != '01' or crc_start is None:
            raise ValueError('Missing format/checksum field.')
        expected = f'{crc_hqx(payload[:crc_start+4].encode(), 0xFFFF):04X}'
        result['crc_valid'] = expected == values['63'].upper()
        result['structural_check_passed'] = result['crc_valid']
        if not result['crc_valid']:
            result['error'] = 'Checksum mismatch. This can indicate corruption; it is not proof of fraud.'
        result['fields'] = {label: values[tag] for tag, label in
                            [('53','currency_code'),('54','amount'),('58','country'),('59','displayed_name'),('60','city')]
                            if tag in values}
        # Never return embedded account identifiers from tags 26-51 in this starter.
    except ValueError as exc:
        result['error'] = str(exc)
    return result
