from pathlib import Path
import numpy as np
import scipy
import scipy.interpolate
import logging
from concurrent.futures import ThreadPoolExecutor

from mmwave import schemas

_logger = logging.getLogger(__name__)
rx_tabel = {  # RX channel order on TI 4-chip cascade EVM
    "slave3": np.asarray([0, 1, 2, 3]),
    "master": np.asarray([4, 5, 6, 7]),
    "slave2": np.asarray([8, 9, 10, 11]),
    "slave1": np.asarray([12, 13, 14, 15]),
}  # 这里不知道为什么和手册对不上 手册是 slave2 master slave3 slave1


def get_idx_info(idx_file: Path):
    dt = np.dtype(
        [
            ("tag", np.uint32),
            ("version", np.uint32),
            ("flags", np.uint32),
            ("numIdx", np.uint32),
            ("size", np.uint64),
        ]
    )
    header = np.fromfile(idx_file, dtype=dt, count=1)[0]

    dt = np.dtype(
        [
            ("tag", np.uint16),
            ("version", np.uint16),
            ("flags", np.uint32),
            ("width", np.uint16),
            ("height", np.uint16),
            ("_meta0", np.uint32),
            ("_meta1", np.uint32),
            ("_meta2", np.uint32),
            ("_meta3", np.uint32),
            ("size", np.uint32),
            ("timestamp", np.uint64),
            ("offset", np.uint64),
        ]
    )
    data = np.fromfile(idx_file, dtype=dt, count=-1, offset=24)
    return header, data


def get_data_files_path(inputdir: Path, device: str):
    """Load the recordings of the radar chip provided in argument.

    Arguments:
        inputdir: Input directory to read the recordings from
        device: Name of the device

    Return:
        Dictionary containing the data and index files
    """
    inputdir = Path(inputdir)
    data = sorted(inputdir.glob(f"{device}*_data.bin"))
    idx = sorted(inputdir.glob(f"{device}*_idx.bin"))
    if len(data) == 0 or len(idx) == 0:
        raise FileNotFoundError(f"No data or index files found for {device} in the input directory")
    elif len(data) != len(idx):
        _logger.error(
            f"[ERROR]: Missing {device} data or index file!\n"
            "Please check your recordings!"
            "\nYou must have the same number of "
            "'*data.bin' and '*.idx.bin' files."
        )
        raise ValueError("Number of data and index files do not match")
    return data, idx


def load_bin_file(bin_file: Path, samples_num: int, chrips_num: int, chrip_idx: int = 1):
    """Re-Format the raw radar ADC recording.
    The raw recording from each device is merge together to create
    separate recording frames corresponding to the MIMO configuration.
    Arguments:
        bin_file: Path to the recording file of the device
        samples_num: Number of ADC samples per chirp
        chrips_num: Number of chrips per frame
    Return:
        The index number of the last frame generated
    Note:
        Considering the AWR mmwave radar kit from Texas Instrument used,
        The following information can be infered:
            - Number of cascaded radar chips: 4
            - Number of RX antenna per chip: 4
            - Number of TX antenna per chip: 3
            - Number of signal measured per ADC samples: 2
                - In-phase signal (I)
                - Quadrature signal (Q)
    """
    nwave = 2  # I and Q
    devices_num = 4  # 级联设备数目
    ntx = 3  # 发射天线数目
    nrx = 4  # 接收天线数目
    nitems = chrips_num * ntx * devices_num * samples_num * nrx * nwave

    bin_file_array = np.memmap(bin_file, dtype=np.int16, mode="r")
    # bin_file_array = np.fromfile(bin_file, dtype=np.int16)
    assert bin_file_array.shape[0] % nitems == 0

    res = bin_file_array.reshape(-1, nitems)
    res = bin_file_array.reshape(-1, chrips_num, ntx * devices_num, samples_num, nrx, nwave)
    # (frame , chrips_num , ntx * devices_num , samples_num , nrx , 2)

    res = np.transpose(res, (0, 1, 2, 4, 3, 5))
    return res


def get_data_idx(idxs_path: list, offset_time: float, frame_periodicity: float):
    all_frame_time = []
    for idx_path in idxs_path:
        header_info, frame_info = get_idx_info(idx_path)
        # _logger.info(f"header_info: {header_info}")
        frame_time = np.array([i[-2] for i in frame_info])
        all_frame_time.append(frame_time)

    data_idx = np.concatenate(all_frame_time)

    data_idx = (data_idx - data_idx[0] + offset_time * 1e6) / 1000 / frame_periodicity
    # data_idx = (data_idx + offset_time * 1e6) / 1000 / frame_periodicity

    data_idx = np.rint(data_idx).astype(int)
    return data_idx


def get_bracket_idx(input_dir: Path, x_sample_num: int, frame_periodicity: float):
    time_info = np.loadtxt(input_dir / "timestamps.txt")
    offset_time = time_info[-1][0]
    time_info = time_info[0:-1]
    bracket_idx = []
    for t0, t1 in time_info:
        start = t0 * 1000 / frame_periodicity
        end = start + x_sample_num
        bracket_idx.append((start, end))
    bracket_idx = np.asarray(bracket_idx)
    bracket_idx = np.rint(bracket_idx).astype(int)
    return bracket_idx, offset_time


def iter_all_frame(bin_files_path: list[Path], samples_num: int, chrips_num: int):
    for bin_file_path in bin_files_path:
        bin_array = load_bin_file(bin_file_path, samples_num, chrips_num)
        yield bin_array


def interpolate_zero(data: np.ndarray):
    grids = [np.arange(dim) for dim in data.shape]

    interpolator = scipy.interpolate.RegularGridInterpolator(grids, data, method="linear", bounds_error=False, fill_value=0)

    indices = np.array(np.indices(data.shape)).reshape(len(data.shape), -1).T
    zero_points = indices[np.ravel(data) == 0]

    interpolator_values = interpolator(zero_points)
    for idx, value in zip(zero_points, interpolator_values):
        data[tuple(idx)] = value
    return data


class MMWFrame:
    def __init__(self, bin_files_path: Path, samples_num: int, chrips_num: int, data_idx: np.ndarray):
        self.bin_files_path = bin_files_path
        self.samples_num = samples_num
        self.chrips_num = chrips_num
        self.data_idx = data_idx

        self.all_frames_iter = iter_all_frame(bin_files_path, samples_num, chrips_num)
        self.bin_array: np.ndarray = next(self.all_frames_iter)
        self.shape = self.bin_array.shape[1:]
        self.dtype = self.bin_array.dtype

        self.frame_offset = 0
        self.stop_iteration_flag = False

    def _get_next_bin_array(self):
        try:
            self.bin_array = next(self.all_frames_iter)
            return self.bin_array
        except StopIteration:
            self.stop_iteration_flag = True

    def __getitem__(self, i) -> np.ndarray:
        bin_array = self.bin_array
        bin_len = bin_array.shape[0]
        frame_offset = self.frame_offset
        data_idx = self.data_idx

        if isinstance(i, tuple):
            i, args = i[0], i[1:]
        else:
            args = ()

        if isinstance(i, slice):
            b_start, b_end, step = i.start, i.stop, i.step
        elif isinstance(i, int):
            return bin_array[i - self.frame_offset, *args]
        else:
            raise ValueError("Index must be int or slice")

        start, end = np.searchsorted(data_idx, [b_start, b_end])

        mmw_idx = data_idx[start:end] - b_start

        start, end = start - frame_offset, end - frame_offset

        line_frames = bin_array[start:end]

        if end >= bin_len:
            bin_array = self._get_next_bin_array()
            if bin_array is not None:
                start, end = max(0, start - bin_len), end - bin_len
                line_frames = np.concatenate((line_frames, bin_array[start:end]))
                self.frame_offset += bin_len

        line_frames = line_frames[:, *args]
        new_line_frames = np.zeros((b_end - b_start, *line_frames.shape[1:]), dtype=line_frames.dtype)
        new_line_frames[mmw_idx] = line_frames[:]
        return new_line_frames


def turn_device_frame(
    all_frames: np.ndarray,
    mmw_frames: MMWFrame,
    rx_idx: np.ndarray,
    chirp_idx: int,
    bracket_idx: np.ndarray,
    next_line_reverse=False,
):
    from tqdm.auto import trange

    for i in trange(bracket_idx.shape[0]):
        start, end = bracket_idx[i]
        line_frames = mmw_frames[start:end, chirp_idx].transpose(2, 1, 0, 3, 4)
        if next_line_reverse and (i % 2 == 1):
            all_frames[rx_idx, :, i] = line_frames[::-1]
        else:
            all_frames[rx_idx, :, i] = line_frames

        if mmw_frames.stop_iteration_flag:
            break


def check_data_idx(input_dir: Path):
    import matplotlib.pyplot as plt

    for idx_num in ["master", "slave1", "slave2", "slave3"]:
        idxs_path = sorted(input_dir.glob(f"{idx_num}*_idx.bin"))
        all_frame_time = []
        for idx_path in idxs_path:
            header_info, frame_info = get_idx_info(idx_path)
            frame_time0 = frame_info[0][-2] * 1e-6
            frame_time1 = frame_info[-1][-2] * 1e-6
            print(frame_time0, frame_time1)
            frame_time = np.array([i[-2] for i in frame_info]) * 1e-6
            all_frame_time.append(frame_time)
        frame_time = np.concatenate(all_frame_time)
        dframe_time = frame_time[1:] - frame_time[:-1]
        plt.plot(dframe_time)
    plt.grid()
    plt.show()


def turn_frame(input_dir: Path, cfg: schemas.MMWConfig):
    adc_samples_num = cfg.mimo.profile.numAdcSamples  # number of ADC samples per chirp
    chrips_num = cfg.mimo.frame.numLoops  # number of chrips per frame
    chrip_idx = min(1, chrips_num - 1)  # use chirp 1 if chirp num big than 1
    _logger.info(f"chrips_num: {chrips_num}")
    frame_periodicity = cfg.mimo.frame.framePeriodicity  # stampe frame time in ms
    _logger.info(f"frame_periodicity: {frame_periodicity}")
    x_sample_num = cfg.bracket.profile.col
    y_sample_num = cfg.bracket.profile.row
    offset_time = cfg.bracket.profile.offset_time  # 手动偏移校准
    next_line_reverse = cfg.bracket.profile.next_line_reverse
    _logger.info(f"next_line_reverse: {next_line_reverse}")
    num_frames = cfg.mimo.frame.numFrames
    _logger.info(f"num_frames: {num_frames}, need record time:{num_frames * frame_periodicity / 1000}s")

    bracket_idx, _ = get_bracket_idx(input_dir, x_sample_num, frame_periodicity)
    array_shape = (16, 12, y_sample_num, x_sample_num, adc_samples_num, 2)

    all_mmw_array = np.zeros(array_shape, dtype=np.int16)

    bin_files_path, idxs_path = get_data_files_path(input_dir, "master")
    data_idx = get_data_idx(idxs_path, offset_time, frame_periodicity)
    _logger.info(f"record time:{data_idx[-1] * frame_periodicity / 1000}s")

    def ithread(device_name):
        mmw_frame = MMWFrame(bin_files_path, adc_samples_num, chrips_num, data_idx)
        turn_device_frame(all_mmw_array, mmw_frame, rx_tabel[device_name], chrip_idx, bracket_idx, next_line_reverse)

    with ThreadPoolExecutor() as executor:
        for device_name in ["master", "slave1", "slave2", "slave3"]:
            executor.submit(ithread, device_name)

    np.save(input_dir / "all_mmw_array.npy", all_mmw_array)


def main():
    import sys
    from rich.console import Console
    from .util import load_config

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print = Console().print

    args = sys.argv[1:]
    if args:
        input_dir = Path(args[0])
    else:
        input_dir = Path("../mmwave_postproc/outdoor_20250422_222653")
    _logger.info(f"read file from {input_dir}")

    cfg = load_config(input_dir / "config.toml")
    turn_frame(input_dir, cfg)


if __name__ == "__main__":
    main()
