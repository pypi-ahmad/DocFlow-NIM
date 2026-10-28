"""Decoded-image bounds shared by document loading and the local worker."""

MAX_IMAGE_PIXELS = 40_000_000


def check_image_size(size):
    """Reject dimensions before allocating an RGB copy of an input frame."""
    width, height = size
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise ValueError("Images must have positive dimensions and at most 40 megapixels.")
