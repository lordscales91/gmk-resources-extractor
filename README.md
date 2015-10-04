GMK Resource Extractor
====
This program is designed to provide a way to recover your lost resource files for your own Game Maker Studio game.

**Note** it requires the Python Image Library (PIL), more specifically the Pillow port, to install it use:

	pip install Pillow 

Disclaimer
----
I'm not responsible of any unintended use of this program, use it at your own risk.

Usage
----
	python launch.py <data.win> [output_dir]
	[-ignore {sound,textures,sprites} [{sound,textures,sprites} ...]]
	[--convert]
	[-h, --help]

*&lt;data.win&gt;* refers to the main resource file usually called with this name.


*[output_dir]* Optional base directory for the recovered resources, it defaults to "data"


*[-ignore]* Optionally you can specify which should be ignored, therefore not saved to disk

*[--convert]* Specifies if the metadata should be processed to get the final resources (Ex. get the sprites)

Progress
----
So far this utility is able to recover audio and texture files, as well as sprite metadata, also it is able to get the sprites from the metadata.
