import numpy as np
import matplotlib.pyplot as plt

from .matlab_cmap import parula_map
from functools import partial

pad = partial(np.pad, mode="constant", constant_values=0)


def align_matrix(a: np.ndarray, b: np.ndarray):
    """Align two matrix by padding zeros."""
    pl = b.shape[0] - a.shape[0]
    pad_width = np.array(((pl // 2, pl - pl // 2), (0, 0)))
    if pl > 0:
        a = pad(a, pad_width)
    else:
        b = pad(b, -pad_width)

    pl = b.shape[1] - a.shape[1]
    pad_width = np.array(((0, 0), (pl // 2, pl - pl // 2)))
    if pl > 0:
        a = pad(a, pad_width)
    else:
        b = pad(b, -pad_width)
    return a, b


def rma(sarData, dx, dy, R, k):
    nFFTspace = 512  # Number of FFT points for Spatial-FFT

    wSx, wSy = 2 * np.pi / np.array([dx, dy]) / 1e-3  # Sampling space for Target Domain
    kX = np.linspace(-wSx / 2, wSx / 2, nFFTspace)[np.newaxis, :]  # kX-Domain
    kY = np.linspace(-wSy / 2, wSy / 2, nFFTspace)[:, np.newaxis]  # kY-Domain
    K = (2 * k) ** 2 - (kX**2 + kY**2)  # 求kz
    K = np.sqrt(K, where=K > 0, out=np.zeros_like(K))

    phaseFactor = np.fft.fftshift(K * np.exp(-1j * R * K))

    sarData, phaseFactor = align_matrix(sarData, phaseFactor)

    sarDataFFT = np.fft.fft2(sarData, s=[nFFTspace, nFFTspace])
    sarImage_2DRMA = np.fft.ifft2(sarDataFFT * phaseFactor)
    return sarImage_2DRMA


def unwarp_2d(echo_data):
    Echo_abs = np.abs(echo_data)
    Echo_abs_log = 40 * np.log10(Echo_abs / np.max(Echo_abs))
    Echo_phase = np.zeros_like(Echo_abs_log)

    Echo_mask = Echo_abs_log > -160
    Echo_phase[Echo_mask] = np.angle(echo_data)[Echo_mask]
    Echo_phase = np.unwrap(np.unwrap(Echo_phase, axis=1), axis=0)
    Echo_phase[~Echo_mask] = 0
    return Echo_phase


def cult_zero_bound(data, arr: np.ndarray):
    # 获取非零区域的上下左右边界
    rows, cols = np.where(arr != 0)
    top = rows.min()
    bottom = rows.max()
    left = cols.min()
    right = cols.max()

    return data[top : bottom + 1, left : right + 1]


def echo_plot(echo: np.ndarray, title: str, dx=1, dy=2, rma=False):
    # plt.close()
    row, col = echo.shape[0], echo.shape[1]
    rw = dx * col / 1000
    rh = dy * row / 1000
    if rma:
        raido = (dy, dx)
    else:
        raido = (rh * 1000, rw * 1000)
    aspact = (raido[0] / (echo.shape[0] - 1)) / (raido[1] / (echo.shape[1] - 1))

    fignum = 2
    plt.figure(figsize=[15, 6])

    plt.subplot(1, fignum, 1)
    Echo_abs = np.abs(echo)
    Echo_abs_log = 40 * np.log10(Echo_abs / np.max(Echo_abs))

    plt.imshow(
        Echo_abs_log,
        cmap=parula_map,
        vmin=-60,
        vmax=0,
        aspect=aspact,
        origin="lower",
    )
    plt.axis("off")
    plt.colorbar()
    plt.grid()
    plt.title(f"{title} abs Image")

    plt.subplot(1, fignum, 2)
    #
    # plt.imshow(np.angle(echo,deg=True), cmap=parula_map, aspect=aspact.origin="lower")
    Echo_phase = np.arcsin(np.imag(echo / Echo_abs)) / np.pi * 180

    plt.imshow(Echo_phase, cmap=parula_map, aspect=aspact, origin="lower")
    plt.clim(-90, 90)
    plt.grid()
    plt.axis("off")
    plt.colorbar()
    plt.title(f"{title} phi Image")
    # plt.show()
