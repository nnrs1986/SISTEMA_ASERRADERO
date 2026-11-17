from django.utils.html import format_html, format_html_join


CODE128_PATTERNS = (
    '11011001100', '11001101100', '11001100110', '10010011000', '10010001100',
    '10001001100', '10011001000', '10011000100', '10001100100', '11001001000',
    '11001000100', '11000100100', '10110011100', '10011011100', '10011001110',
    '10111001100', '10011101100', '10011100110', '11001110010', '11001011100',
    '11001001110', '11011100100', '11001110100', '11101101110', '11101001100',
    '11100101100', '11100100110', '11101100100', '11100110100', '11100110010',
    '11011011000', '11011000110', '11000110110', '10100011000', '10001011000',
    '10001000110', '10110001000', '10001101000', '10001100010', '11010001000',
    '11000101000', '11000100010', '10110111000', '10110001110', '10001101110',
    '10111011000', '10111000110', '10001110110', '11101110110', '11010001110',
    '11000101110', '11011101000', '11011100010', '11011101110', '11101011000',
    '11101000110', '11100010110', '11101101000', '11101100010', '11100011010',
    '11101111010', '11001000010', '11110001010', '10100110000', '10100001100',
    '10010110000', '10010000110', '10000101100', '10000100110', '10110010000',
    '10110000100', '10011010000', '10011000010', '10000110100', '10000110010',
    '11000010010', '11001010000', '11110111010', '11000010100', '10001111010',
    '10100111100', '10010111100', '10010011110', '10111100100', '10011110100',
    '10011110010', '11110100100', '11110010100', '11110010010', '11011011110',
    '11011110110', '11110110110', '10101111000', '10100011110', '10001011110',
    '10111101000', '10111100010', '11110101000', '11110100010', '10111011110',
    '10111101110', '11101011110', '11110101110', '11010000100', '11010010000',
    '11010011100',
)
CODE128_STOP = '1100011101011'
MODULE_WIDTH = 2
QUIET_ZONE = 10


def code128_svg(value):
    """Render a Code 128-B barcode for an ASCII package identifier."""
    try:
        data_codes = [ord(character) - 32 for character in value]
    except TypeError as error:
        raise ValueError('El código de barras debe ser texto.') from error

    if not data_codes or any(not 0 <= code <= 94 for code in data_codes):
        raise ValueError('El código de barras solo admite caracteres ASCII imprimibles.')

    checksum = (104 + sum(position * code for position, code in enumerate(data_codes, 1))) % 103
    encoded = ''.join(
        CODE128_PATTERNS[code]
        for code in (104, *data_codes, checksum)
    ) + CODE128_STOP

    bars = []
    position = QUIET_ZONE
    index = 0
    while index < len(encoded):
        if encoded[index] == '0':
            index += 1
            continue
        start = index
        while index < len(encoded) and encoded[index] == '1':
            index += 1
        bars.append((position + start * MODULE_WIDTH, (index - start) * MODULE_WIDTH))

    width = (len(encoded) + QUIET_ZONE * 2) * MODULE_WIDTH
    bar_elements = format_html_join(
        '',
        '<rect x="{}" y="0" width="{}" height="50" fill="#111"/>',
        bars,
    )
    return format_html(
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="72" '
        'viewBox="0 0 {} 72" role="img" aria-label="Código de barras {}">'
        '{}<text x="50%" y="68" text-anchor="middle" '
        'font-family="sans-serif" font-size="14">{}</text></svg>',
        width,
        width,
        value,
        bar_elements,
        value,
    )
