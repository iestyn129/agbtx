from .palette import Palette
from io import BytesIO
from math import ceil
from PIL import Image
from typing import TYPE_CHECKING, Any, Self
if TYPE_CHECKING:
	from PIL._imaging import PixelAccess
else:
	type PixelAccess = Any

__all__: list[str] = [
	'TILE_WIDTH',
	'TILE_HEIGHT',
	'TILE_LEN',
	'TILE_SIZE',
	'MAX_TILES',
	'TILES_PER_ROW',
	'Sprite'
]

TILE_WIDTH: int = 8
TILE_HEIGHT: int = TILE_WIDTH
TILE_LEN: int = TILE_WIDTH * TILE_HEIGHT
TILE_SIZE: int = TILE_LEN // 2
MAX_TILES: int = 32 * 32
TILES_PER_ROW: int = 32


class Sprite:
	def __init__(self, tiles: list[list[list[int]]]) -> None:
		if len(tiles) <= 0:
			raise ValueError('Tiles must be non-empty')

		if len(tiles) > MAX_TILES:
			raise ValueError(f'Tiles exceed GBA limit of {MAX_TILES} ({len(tiles)} tiles)')

		for tile_idx, tile in enumerate(tiles):
			if len(tile) != TILE_HEIGHT:
				raise ValueError(f'Invalid tile at index {tile_idx}, has {len(tile)} rows')

			for row_idx, row in enumerate(tile):
				if len(row) != TILE_WIDTH:
					raise ValueError(f'Invalid tile at index {tile_idx}, row {row_idx} has {len(row)} pixels')

		self.tiles: list[list[list[int]]] = tiles

	@classmethod
	def from_image(cls, img: Image.Image) -> Self:
		if img.mode != 'P':
			raise ValueError('Image must be indexed (aka use palettes)')

		if img.width % TILE_WIDTH != 0 or img.height % TILE_HEIGHT != 0:
			raise ValueError(f'Image must be composed of {TILE_WIDTH}x{TILE_HEIGHT}px tiles')

		tiles: list[list[list[int]]] = []
		pixels: PixelAccess = img.load()

		for tile_y in range(0, img.height, TILE_HEIGHT):
			for tile_x in range(0, img.width, TILE_WIDTH):
				tile: list[list[int]] = []

				for y in range(TILE_HEIGHT):
					row: list[int] = []

					for x in range(TILE_WIDTH):
						row.append(int(pixels[tile_x + x, tile_y + y]))

					tile.append(row)

				tiles.append(tile)

		return cls(tiles)

	@classmethod
	def from_4bpp(cls, data: bytes) -> Self:
		if len(data) % TILE_SIZE != 0:
			raise ValueError(f'Invalid 4BPP data, not composed of {TILE_WIDTH}x{TILE_HEIGHT}px tiles')

		tiles: list[list[list[int]]] = []

		for tile_idx in range(0, len(data), TILE_SIZE):
			tile: list[list[int]] = []
			row: list[int] = []

			for i in range(TILE_SIZE):
				pixels: int = data[tile_idx + i]
				low: int = pixels & 0b00001111
				high: int = (pixels & 0b11110000) >> 4

				row.extend([low, high])

				if len(row) >= TILE_WIDTH:
					tile.append(row)
					row = []

			tiles.append(tile)

		return cls(tiles)

	@property
	def num_tiles(self) -> int:
		return len(self.tiles)

	def to_image(self, palette: Palette, pad: bool = True) -> Image.Image:
		tiles: list[list[list[int]]] = self.tiles

		if pad:
			tiles = list(self.tiles)
			while len(tiles) % TILES_PER_ROW != 0:
				tiles.append([[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)])

		tpr: int = min(TILES_PER_ROW, len(tiles))
		img_width: int = tpr * TILE_WIDTH
		img_height: int = ceil(len(tiles) / tpr) * TILE_HEIGHT
		img: Image.Image = Image.new('P', (img_width, img_height))
		img.putpalette(palette.to_list(pad))
		pixels: PixelAccess = img.load()

		for tile_idx, tile in enumerate(tiles):
			tile_x: int = (tile_idx % tpr) * TILE_WIDTH
			tile_y: int = (tile_idx // tpr) * TILE_HEIGHT

			for pixel_y, row in enumerate(tile):
				for pixel_x, pixel in enumerate(row):
					pixels[tile_x + pixel_x, tile_y + pixel_y] = pixel

		return img

	def to_4bpp(self) -> bytes:
		with BytesIO() as fp:
			for tile in self.tiles:
				for row in tile:
					for pixel_idx in range(0, len(row), 2):
						low: int = row[pixel_idx] & 0b00001111
						high: int = (row[pixel_idx + 1] & 0b00001111) << 4

						fp.write((low | high).to_bytes(1))

			return fp.getvalue()
