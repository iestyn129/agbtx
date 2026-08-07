from copy import deepcopy
from struct import pack
from typing import Sequence, Self
import re

__all__: list[str] = [
	'Palette'
]

PAL_LEN: int = 16
COLOUR_SIZE: int = 3
PAL_SIZE: int = PAL_LEN * COLOUR_SIZE
MAX_PALETTES: int = 16


class Palette:
	def __init__(self, palettes: list[list[tuple[int, int, int]]]) -> None:
		if len(palettes) <= 0:
			raise ValueError('Palettes must be non-empty')

		if len(palettes) > MAX_PALETTES:
			raise ValueError(f'Palettes exceed GBA limit of {MAX_PALETTES} ({len(palettes)} palettes)')

		for pal_idx, palette in enumerate(palettes):
			if len(palette) > PAL_LEN:
				raise ValueError(f'Invalid palette at index {pal_idx}, has{len(palette)} colours')

		self.palettes: list[list[tuple[int, int, int]]] = palettes

	@classmethod
	def from_rgb888(cls, data: Sequence[int]) -> Self:
		if len(data) > 256 * 3:
			raise ValueError(f'Data exceeds 256 colour (16 palette) limit ({len(data) // 3} colours)')

		if len(data) % 3 != 0:
			raise ValueError(f'Data must be multiple of 3')

		palettes: list[list[tuple[int, int, int]]] = []

		for pal_idx in range(0, len(data), PAL_SIZE):
			palette: list[tuple[int, int, int]] = []

			for colour_idx in range(0, min(len(data) - pal_idx, PAL_SIZE), 3):
				palette.append((
					data[pal_idx + colour_idx] & 0b11111000,
					data[pal_idx + colour_idx + 1] & 0b11111000,
					data[pal_idx + colour_idx + 2] & 0b11111000
				))

			palettes.append(palette)

		return cls(palettes)

	@classmethod
	def from_c(cls, data: str) -> Self:
		colors = [
			(int(x[0:2], 16), int(x[2:4], 16), int(x[4:6], 16))
			for x in re.findall(r"TO_RGB555\(0x([0-9a-fA-F]{6})\)", data)
		]

		palettes: list[list[tuple[int, int, int]]] = []
		palette: list[tuple[int, int, int]] = []

		for colour in colors:
			palette.append(colour)

			if len(palette) >= PAL_LEN:
				palettes.append(palette)
				palette = []

		return cls(palettes)

	@classmethod
	def from_windows(cls, data: bytes) -> Self:
		data = data[24:]

		palettes: list[list[tuple[int, int, int]]] = []

		for pal_idx in range(0, len(data), PAL_LEN * 4):
			palette: list[tuple[int, int, int]] = []

			for colour_idx in range(0, min(len(data) - pal_idx, PAL_LEN * 4), 4):
				palette.append((
					data[pal_idx + colour_idx] & 0b11111000,
					data[pal_idx + colour_idx + 1] & 0b11111000,
					data[pal_idx + colour_idx + 2] & 0b11111000
				))

			palettes.append(palette)

		return cls(palettes)

	def to_list(self, pad: bool = True) -> list[int]:
		data: list[int] = []

		for palette in self.palettes:
			if pad:
				palette = deepcopy(palette)
				while len(palette) % PAL_LEN != 0:
					palette.append((0, 0, 0))

			for colours in palette:
				for colour in colours:
					data.append(colour)

		return data

	def save_as_rgb888(self, filepath: str, pad: bool = True) -> None:
		with open(filepath, 'wb') as fp:
			fp.write(bytes(self.to_list(pad)))

	def save_as_c(self, filepath: str, pal_name: str, pad: bool = True) -> None:
		with open(filepath, 'w') as fp:
			fp.writelines([
				'#include "global.h"\n',
				'#include "graphics.h"\n',
				'\n',
				f'Palette {pal_name}[] = {{\n'
			])

			for i, palette in enumerate(self.palettes):
				if pad:
					palette = deepcopy(palette)
					while len(palette) % PAL_LEN != 0:
						palette.append((0, 0, 0))

				fp.write(f'\t/* palette {i:02} */ {{\n')

				for j, colour in enumerate(palette):
					red: int = colour[0]
					green: int = colour[1]
					blue: int = colour[2]

					fp.write(
						f'\t\t/* {j:02} */ TO_RGB555(0x{red:02x}{green:02x}{blue:02x})'
						f'{"" if j == (len(palette) - 1) else ","}\n'
					)

				fp.write(f'\t}}{"" if i == (len(self.palettes) - 1) else ","}\n')

			fp.write('};\n')

	def save_as_windows(self, filepath: str, pad: bool = True) -> None:
		colours: list[tuple[int, int, int]] = []

		for palette in self.palettes:
			colours.extend(palette)

		if pad:
			while len(colours) % PAL_LEN != 0:
				colours.append((0, 0, 0))

		palette_size: int = len(colours)
		data_size: int = palette_size * 4
		file_size: int = data_size + 24

		with open(filepath, 'wb') as fp:
			fp.write(b'RIFF')
			fp.write(pack("<I", file_size - 8))
			fp.write(b'PAL ')
			fp.write(b'data')
			fp.write(pack("<I", file_size - 20))
			fp.write(pack('<HH', 3, palette_size))
			fp.write(b'FUCK') # gimp, oh gimp, why must you curse me this way

			for red, green, blue in colours:
				fp.write(pack('BBBB', red, green, blue, 0))
