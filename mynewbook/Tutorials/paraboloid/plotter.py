import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import MultipleLocator
import numpy as np

import glob
from PIL import Image


def create_rotating_plot(rotation_range):
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

    # Make data.
    X = np.arange(-50, 50, 1.0)
    Y = np.arange(-50, 50, 1.0)
    X, Y = np.meshgrid(X, Y)
    Z = (X - 3.0) ** 2 + X * Y + (Y + 4.0) ** 2 - 3.0

    # Plot the surface.
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, linewidth=0, antialiased=False)

    # Customize the z axis.
    ax.set_zlim(-27.0, 8000.0)
    # ax.zaxis.set_major_locator(MultipleLocator(1000))
    ax.zaxis.set_ticklabels([])
    # A StrMethodFormatter is used automatically
    # ax.zaxis.set_major_formatter("{x:.02f}")
    # Add a color bar which maps values to colors.
    cbar = fig.colorbar(
        surf,
        shrink=0.5,
        aspect=5,
        label="f(x,y)",
    )
    cbar.set_ticks([-27.0, 2000.0, 4000.0, 6000.0])
    cbar.set_ticklabels([-27.0, 2000.0, 4000.0, 6000.0])

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Surface of the paraboloid", fontsize=18)
    # plt.show()

    # if add_values:
    #     vals = np.array(add_values)
    #     x = vals[:, 0]
    #     y = vals[:, 1]
    #     z = (x - 3.0) ** 2 + x * y + (y + 4.0) ** 2 - 3.0
    #     ax.stem(x, y, z)

    for angle in rotation_range:
        ax.view_init(30, angle)
        plt.draw()
        plt.savefig(f"./paraboloid_{angle:03d}.png")


def create_plot_overlay(unconstrained, constrained):

    fig, ax = plt.subplots()
    # Make data.
    X = np.arange(-10, 10, 1.0)
    Y = np.arange(-20, 15, 1.0)
    X, Y = np.meshgrid(X, Y)
    Z = (X - 3.0) ** 2 + X * Y + (Y + 4.0) ** 2 - 3.0

    contour = plt.contour(X, Y, Z, levels=np.linspace(np.min(Z), np.max(Z), 50))

    cbar = fig.colorbar(
        contour,
        aspect=10,
        label="f(x,y)",
    )
    cbar.set_ticks([-27.0, 0.0, 200.0, 400.0, 600.0])
    cbar.set_ticklabels([-27.0, 0.0, 200.0, 400.0, 600.0])
    plt.xlabel("x")
    plt.ylabel("y")
    # plt.show()

    xp = []
    yp = []
    plt.title("Unconstrained optimisation", fontsize=18)
    for ii, p in enumerate(unconstrained):
        xp.append(p[0])
        yp.append(p[1])
        ax.plot(xp, yp, "-ob", label="slsqp")
        ax.legend()
        plt.draw()
        plt.savefig(f"./paraboloid_{ii:03d}.png")
        ax.lines.pop(0)

    xp = []
    yp = []
    plt.title("Constrained optimisation", fontsize=18)
    ax.plot(X[0].tolist(), (-X[0]).tolist(), "-r", label="g = 0")
    for jj, p in enumerate(constrained):
        xp.append(p[0])
        yp.append(p[1])
        ax.plot(xp, yp, "-ob", label="slsqp")
        ax.legend()
        plt.draw()
        plt.savefig(f"./paraboloid_{ii+jj+1:03d}.png")
        ax.lines.pop(1)


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
    # create_rotating_plot(range(0, 360, 10))
    # make_gif("paraboloid_rotation.gif", duration=150, prefix = "paraboloid_")
    # create_plot_overlay(
    #     unconstrained=[
    #         [5.0, 5.0],
    #         [-4.0, -18.0],
    #         [1.64014688, -3.58629131],
    #         [7.26960294, -7.78279492],
    #         [6.66666667, -7.33333333],
    #     ],
    #     constrained=[[5.0, 5.0], [7.0, -7.0]],
    # )
    # make_gif("paraboloid_optimisation.gif", duration=600, prefix = "paraboloid_")
    make_gif("chained_analysis.gif", folder="../to_gif", duration=600, prefix="")
