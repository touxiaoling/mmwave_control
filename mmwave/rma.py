import numpy as np
import matplotlib.pyplot as plt

from .matlab_cmap import parula_map
from functools import partial

pad = partial(np.pad, mode="constant", constant_values=0)


def align_matrix(a: np.ndarray, b: np.ndarray):
    """Align two matrix by padding zeros."""
    pad = partial(np.pad, mode="constant", constant_values=0)
    mshape = len(a.shape)
    for axis in range(mshape):
        pl = b.shape[axis] - a.shape[axis]
        pad_width = np.zeros((mshape, 2), dtype=int)
        pad_width[axis] += np.asarray((pl // 2, pl - pl // 2))
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


def main():
    from pathlib import Path
    import numpy as np
    from scipy import constants as C
    import matplotlib.pyplot as plt
    from mmwave.rma import rma, echo_plot
    from mmwave.util import load_frame
    import sys
    import matplotlib

    matplotlib.use("TKAgg")

    args = sys.argv[1:]
    if args:
        input_dir = Path(args[0])
    else:
        input_dir = Path("../mmwave_postproc/cas_data/outdoor_20250422_222653")

    frame_file, cfg = load_frame(input_dir)

    num_sample = cfg.mimo.profile.numAdcSamples
    adcStartTime = cfg.mimo.profile.adcStartTime  # us
    startFrequency = cfg.mimo.profile.startFrequency * 1e9
    K = cfg.mimo.profile.frequencySlope * 1e12  # Slope const (hz/s)
    Fs = cfg.mimo.profile.adcSamplingFrequency * 1e3  # Sampling rate (sps)

    F0 = startFrequency + adcStartTime * K * 1e-6 + num_sample // 2 / Fs * K  # Center frequency

    dx = cfg.bracket.profile.dx
    dy = cfg.bracket.profile.dy  # Sampling distance at x (horizontal) y (vertical) axis in mm
    row = cfg.bracket.profile.row
    col = cfg.bracket.profile.col

    c = C.c
    Ts = 1 / Fs  # Sampling period
    k = 2 * np.pi * F0 / c  # Wave number
    print(f"k:{k}")
    tx_idx = 1
    rx_idx = 1

    Echo = frame_file[rx_idx, tx_idx, :, :, :, 0] + 1j * frame_file[rx_idx, tx_idx, :, :, :, 1]
    ID_select = 21
    nFFTtime = num_sample  # Number of FFT points for Spatial-FFT
    tI = 183  # mm

    R = c / 2 * (ID_select / (K * Ts * nFFTtime)) - tI / 1000
    Sr: np.ndarray = np.fft.fft(Echo)
    Sr = Sr[:, :, ID_select - 1]
    Sr[Sr == 0] = 1e-10
    echo_plot(Sr, "source", dx, dy)
    plt.show()
    reconstructed_image = rma(Sr, dx, dy, R, k)
    echo_plot(reconstructed_image, "reconstructed_image", dx, dy, rma=True)
    plt.show()
