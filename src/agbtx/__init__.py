from agbtx.palette import Palette
from agbtx.sprite import Sprite
from os import path
from PIL import Image
from rich import print
from typer import Typer, Argument, Option
from typing import Annotated

__all__: list[str] = []


app: Typer = Typer()

palette_type_map: dict[str, str] = {
	'rgb888': '.pal',
	'brg555': '.pal',
	'c': '.c',
	'windows': '.pal'
}

output_type_map: dict[str, str] = {
	'png': '.png',
	'bmp': '.bmp',
	'jpeg': '.jpg',
	'jpg': '.jpg'
}


@app.command()
def s(
	sprite_path: Annotated[str, Argument(
		help='Path to the input sprite. An indexed image by default, '
			 'but a binary file containing 4BPP data when extracting.')
	],
	output_path: Annotated[str, Option(
		'--output-path', '-o',
		help='Path to the output file/folder. When building, always assumed to be a file. '
			 'When extracting, assumed to be a folder, unless a palette index is specified, otherwise a file.',
		show_default=False
	)] = None,
	palette_type: Annotated[str, Option(
		'--palette-type', '-pt',
		help='What kind of palette to output/use, acceptable values are: '
			 '"RGB888", "BGR555", "C", "WINDOWS" (case-insensitive).'
	)] = "RGB888",

	extract: Annotated[bool, Option(
		'--extract', '-x',
		help='If set, extracts the input sprite to an image instead of building one.',
		rich_help_panel='Extracting',
		show_default=False
	)] = False,
	output_type: Annotated[str, Option(
		'--output-type', '-ot',
		help='The type of image to output when extracting, acceptable values are: '
			 '"PNG", "BMP", "JPEG" (case-insensitive).',
		rich_help_panel='Extracting'
	)] = "PNG",
	palette_path: Annotated[str, Option(
		'--palette-path', '-pp',
		help='Path to the palette to be used when extracting a sprite. If not specified, '
			 'the path will be inferred using the palette type and sprite path.',
		rich_help_panel='Extracting',
		show_default=False
	)] = None,
	palette_index: Annotated[int, Option(
		'--palette-index', '-pi',
		help='The palette index to be used when extracting a sprite. If not specified, all palettes will be used.',
		rich_help_panel='Extracting',
		show_default=False
	)] = None,
) -> None:
	"""For building (and extracting) sprites and their palettes."""
	palette_type = palette_type.lower()
	output_type = output_type.lower()

	if palette_type not in palette_type_map.keys():
		raise ValueError(f'Invalid palette type ({palette_type}) specified')

	if output_type not in output_type_map.keys():
		raise ValueError(f'Invalid output type ({palette_type}) specified')

	if not extract:
		output_name: str = path.splitext(sprite_path)[0]

		if output_path is None:
			output_path = f'{output_name}.4bpp'

		if not output_path.endswith('.4bpp'):
			output_path += '.4bpp'

		palette_path = f'{output_name}{palette_type_map[palette_type]}'

		img: Image.Image = Image.open(sprite_path)

		if img.mode != 'P':
			print(f'[bold red]Warning: image mode is {img.mode}, quantizing to 16 colours![/bold red]')

		img_palette: Palette = Palette.from_rgb888(img.getpalette())
		img_sprite: Sprite = Sprite.from_image(img)

		match palette_type:
			case 'rgb888':
				img_palette.save_as_rgb888(palette_path)
			case 'brg555': ...
			case 'c':
				img_palette.save_as_c(palette_path, f'{path.basename(output_name)}_pal')
			case 'windows':
				img_palette.save_as_windows(palette_path)

		with open(output_path, 'wb') as fp:
			fp.write(img_sprite.to_4bpp())
	else:
		base_name: str = path.splitext(sprite_path)[0]
		palette_ext: str = palette_type_map[palette_type]
		output_ext: str = output_type_map[output_type]

		if palette_path is None:
			palette_path = f'{base_name}{palette_ext}'

		if output_path is None:
			output_path = f'{base_name}{output_ext}'

		if not output_path.endswith(output_ext):
			output_path += output_ext

		with open(palette_path, 'rb') as fp:
			palette_data: bytes = fp.read()

		pal: Palette
		match palette_type:
			case 'rgb888':
				pal = Palette.from_rgb888(palette_data)
			#case 'brg555': ...
			case 'c':
				pal = Palette.from_c(palette_data.decode())
			case 'windows':
				pal = Palette.from_windows(palette_data)
			case _:
				raise ValueError(f'Invalid palette type ({palette_type}) specified')

		with open(sprite_path, 'rb') as fp:
			sprite_data: bytes = fp.read()

		Sprite.from_4bpp(sprite_data).to_image(pal).save(output_path, output_type)


@app.command()
def t() -> None:
	"""For building (and extracting) tilemaps."""
	...
