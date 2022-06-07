#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Set
from openslide import OpenSlide
from argparse import ArgumentParser


def load_mrxs_files(folder: str) -> Set[Path]:
    return set([str(path) for path in Path(folder).rglob("*.mrxs")])


def read_slides(folders: List[str]) -> List[OpenSlide]:
    data_files = set()
    for folder in folders:
        data_files |= load_mrxs_files(folder)
    return [OpenSlide(file) for file in data_files]


def is_gray(color: tuple):
    (r, g, b, a) = color
    diffs = map(abs, (r-g, r-b, g-b))
    return a == 0 or all(diff <= 10 for diff in diffs)


def is_useful_tile(tile: Image) -> bool:
    tile_copy = tile.copy()
    tile_copy.thumbnail((32, 32))
    _, most_frequent_color = max(tile_copy.getcolors(maxcolors=1024), key=lambda x: x[0])
    return not is_gray(most_frequent_color)


def crop_slide_by_grid(
        slide: OpenSlide,
        level: int,
        size: tuple,
        overlap: float,
        destination_path: str
    ):
    tile_size_x, tile_size_y = size
    full_size_x, full_size_y = slide.level_dimensions[level]
    filename_prefix = slide._filename.split('/')[-1].replace('.mrxs', '')
    stride_x = int(tile_size_x * (1 - overlap))
    stride_y = int(tile_size_y * (1 - overlap))
    n_x = (full_size_x - tile_size_x) // stride_x + 1
    n_y = (full_size_y - tile_size_y) // stride_y + 1
    estimated_number = n_x * n_y
    d = int(np.ceil(np.log10(estimated_number)))
    saved_number = 0
    for i in range(n_x):
        for j in range(n_y):
            top_left = (i * stride_x * 2 ** level, j * stride_y * 2 ** level)
            tile = slide.read_region(
                location=top_left,
                level=level,
                size=size
            )
            if is_useful_tile(tile):
                tile.save(os.path.join(destination_path, f'{filename_prefix}_{saved_number:0{d}}_{level}.png'))
                saved_number += 1


def crop_slides_rejection_sampling(
        slides: List[OpenSlide],
        level: int,
        size: tuple,
        number: int,
        destination_path: str
    ):
    tile_size_x, tile_size_y = size
    saved_number = 0
    d = int(np.ceil(np.log10(number)))
    while saved_number < number:
        slide = np.random.choice(slides)
        filename_prefix = slide._filename.split('/')[-1].replace('.mrxs', '')
        full_size_x, full_size_y = slide.level_dimensions[level]
        top_left_x = np.random.choice(full_size_x - tile_size_x)
        top_left_y = np.random.choice(full_size_y - tile_size_y)
        top_left_rescaled = (top_left_x * 2 ** level, top_left_y * 2 ** level)
        tile = slide.read_region(
            location=top_left_rescaled,
            level=level,
            size=size
        )
        if is_useful_tile(tile):
            tile.save(os.path.join(destination_path, f'{saved_number:0{d}}_{filename_prefix}_{level}.png'))
            saved_number += 1


def run_cropping(args):
    slides = read_slides(args.folders)
    if args.method == 'random':
        crop_slides_rejection_sampling(slides, args.level, args.size, args.number, args.destination)
    elif args.method == 'grid':
        for slide in slides:
            crop_slide_by_grid(slide, args.level, args.size, args.overlap, args.destination)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--method", choices=["random", "grid"],
                        default="random",
                        help="The method of cropping images: 'random' "
                             "for random sampling, 'grid' for cropping "
                             "by grid with possible overlapping")
    parser.add_argument("--folders", dest="folders", nargs="+",
                        help="Paths to slides folders separated by spaces",
                        required=True)
    parser.add_argument("--destination", dest="destination",
                        help="Destination folder",
                        required=True)
    parser.add_argument("--size", dest="size", nargs=2, type=int,
                        help="Tile size components separated by a space",
                        default=(256, 256))
    parser.add_argument("--overlap", dest="overlap", type=float,
                        help="Tiles mutual overlap ratio in grid method",
                        default=0.0)
    parser.add_argument("--number", type=int, dest="number",
                        default=10000, help="Number of images to produce in random method")
    parser.add_argument("--level", type=int, dest="level",
                        default=2, help="Level for image cropping")

    args = parser.parse_args()

    run_cropping(args)
