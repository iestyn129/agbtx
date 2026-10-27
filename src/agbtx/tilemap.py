from .palette import Palette
from .sprite import TILE_WIDTH, TILE_HEIGHT, Sprite
from PIL import Image
from typing import Self

__all__: list[str] = [
	'Tilemap'
]

TILEMAP_SIZES_REGULAR: list[tuple[int, int]] = [
	(32, 32),
	(64, 32),
	(32, 64),
	(64, 64)
]
TILEMAP_LENGTHS_REGULAR: list[int] = [w * h for w, h, in TILEMAP_SIZES_REGULAR]


class Tilemap:
	class Entry:
		def __init__(self,
			tile_idx: int, h_flip: bool = False, v_flip: bool = False, pal_idx: int = 0
		) -> None:
			self.tile_idx: int = tile_idx
			self.h_flip: bool = h_flip
			self.v_flip: bool = v_flip
			self.pal_idx: int = pal_idx

		@classmethod
		def from_bytes(cls, data: bytes) -> Self:
			data = int.from_bytes(data, 'little')

			return cls(
				data & 0b1111111111,
				bool((data & 0b10000000000) >> 10),
				bool((data & 0b100000000000) >> 11),
				(data & 0b1111000000000000) >> 12
			)

		def to_bytes(self) -> bytes:
			return int.to_bytes(
				(self.tile_idx & 0b1111111111) |
				((int(self.h_flip) & 0b1) << 10) |
				((int(self.v_flip) & 0b1) << 11) |
				((self.pal_idx & 0b1111) << 12),
				2, 'little', signed=False
			)

	def __init__(self, tileset: Sprite, tilemap: list[Entry]) -> None:
		self.tileset: Sprite = tileset

		if len(tilemap) not in TILEMAP_LENGTHS_REGULAR:
			raise ValueError(f'Invalid tilemap length: {len(tilemap)}')

		for entry in tilemap:
			if entry.tile_idx >= self.tileset.num_tiles:
				raise ValueError(f'Entry index {entry.tile_idx} is outside of tileset ({self.tileset.num_tiles})')

		self.tilemap: list[Tilemap.Entry] = tilemap

	@classmethod
	def from_image(cls, img: Image.Image, pal_idx: int = 0, *, unique_tiles: list[list[list[int]]] | None = None) -> Self:
		if (img.width // TILE_WIDTH, img.height // TILE_HEIGHT) not in TILEMAP_SIZES_REGULAR:
			raise ValueError(
				f'Invalid source image size: {img.width}x{img.height}px '
				f'({img.width // TILE_WIDTH}x{img.height // TILE_HEIGHT} tiles)'
			)

		source_sprite: Sprite = Sprite.from_image(img)
		if unique_tiles is None:
			unique_tiles = [[[0] * TILE_WIDTH] * TILE_HEIGHT]
		tilemap: list[Tilemap.Entry] = []

		for tile in source_sprite.tiles:
			if tile not in unique_tiles:
				unique_tiles.append(tile)

			tilemap.append(Tilemap.Entry(unique_tiles.index(tile), pal_idx=pal_idx))

		return cls(Sprite(unique_tiles), tilemap)

	@classmethod
	def from_tilemap(cls, tileset: Sprite, data: bytes) -> Self:
		if len(data) // 2 not in TILEMAP_LENGTHS_REGULAR:
			raise ValueError(f'Invalid tilemap length: {len(data) // 2}')

		tilemap: list[Tilemap.Entry] = []

		for i in range(0, len(data), 2):
			tilemap.append(Tilemap.Entry.from_bytes(data[i:i + 2]))

		return cls(tileset, tilemap)

	def save_tilemap(self, filename: str) -> None:
		with open(filename, 'wb') as fp:
			for entry in self.tilemap:
				fp.write(entry.to_bytes())

	def to_image(self, palette: Palette) -> Image.Image:
		tiles: list[list[list[int]]] = []

		for entry in self.tilemap:
			tiles.append(self.tileset.tiles[entry.tile_idx])

		return Sprite(tiles).to_image(palette)
