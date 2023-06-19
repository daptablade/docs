""" Create animation .gif from openfoam animation export. 
    Set `folder` to path with exported .png files, then execute this script."""

import glob
from PIL import Image


def make_gif(name, duration, folder=None, prefix=None):
    p = ""
    if folder:
        p = folder + "/"
        name = folder + "/" + name
    if prefix:
        p = p + prefix
    files = sorted(glob.glob(p + "*.png"))
    print(files)
    frames = [Image.open(image) for image in files]
    frame_one = frames[0]
    frame_one.save(
        name,
        format="GIF",
        append_images=frames,
        save_all=True,
        duration=duration,
        loop=0,
    )


if __name__ == "__main__":
    make_gif(
        "perpendicular_plate_U.gif",
        folder="/home/olivia/perpendicular_plate_animation",
        duration=600,
        prefix="",
    )
