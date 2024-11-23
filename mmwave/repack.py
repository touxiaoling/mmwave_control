from contextlib import contextmanager
from pathlib import Path
import numpy as np
from tempfile import NamedTemporaryFile


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
        print(
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

    # bin_file_array = np.memmap(bin_file, dtype=np.int16, mode="r")
    bin_file_array = np.fromfile(bin_file, dtype=np.int16)
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
        frame_time = np.array([i[-2] for i in frame_info])
        all_frame_time.append(frame_time)

    data_idx = np.concatenate(all_frame_time)

    data_idx = (data_idx - data_idx[0] + offset_time * 1e6) / 1000 / frame_periodicity
    # data_idx = (data_idx + offset_time * 1e6) / 1000 / frame_periodicity

    data_idx = np.astype(np.around(data_idx), int)
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
    bracket_idx = np.array(bracket_idx)
    bracket_idx = np.astype(np.around(bracket_idx), int)
    return bracket_idx, offset_time


def iter_all_frame(bin_files_path: Path, samples_num: int, chrips_num: int):
    for bin_file_path in bin_files_path:
        bin_array = load_bin_file(bin_file_path, samples_num, chrips_num)
        yield bin_array


def turn_device_frame(
    bin_files_path: Path,
    samples_num: int,
    chrips_num: int,
    bracket_idx: np.ndarray,
    data_idx: np.ndarray,
    x_sample_num: int,
):
    all_frames_iter = iter_all_frame(bin_files_path, samples_num, chrips_num)
    bin_array = next(all_frames_iter)
    bin_len = bin_array.shape[0]

    y_sample_num = bracket_idx.shape[0]
    array_shape = (y_sample_num, x_sample_num, *(bin_array.shape[2:]))
    mmw_array = np.zeros(array_shape, dtype=bin_array.dtype)
    frame_offset = 0
    stop_iteration_flag = False
    for i in trange(bracket_idx.shape[0]):
        b_start, b_end = bracket_idx[i]
        start, end = np.searchsorted(data_idx, [b_start, b_end])

        mmw_idx = data_idx[start:end] - b_start

        start, end = start - frame_offset, end - frame_offset
        line_frames = bin_array[start:end]

        if end >= bin_len:
            try:
                bin_array = next(all_frames_iter)

                start, end = max(0, start - bin_len), end - bin_len
                line_frames = np.concatenate((line_frames, bin_array[start:end]))

                frame_offset += bin_len
                bin_len = bin_array.shape[0]
            except StopIteration:
                stop_iteration_flag = True

        mmw_array[i, mmw_idx] = line_frames[:, 1]

        if stop_iteration_flag:
            break

    return mmw_array


def check_data_idx(input_dir: Path):
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


if __name__ == "__main__":
    from rich.console import Console
    import matplotlib.pyplot as plt
    from tqdm import trange

    print = Console().print
    adc_samples_num = 256  # number of ADC samples per chirp
    chrips_num = 4  # number of chrips per frame
    frame_periodicity = 25  # stampe frame time in ms
    x_sample_num = 401
    offset_time = -0.920  # 手动偏移校准

    input_dir = Path("../outdoor_20241121_143316")

    bracket_idx, _ = get_bracket_idx(input_dir, x_sample_num, frame_periodicity)

    for device_name in ["slave3"]:  # ["master", "slave1", "slave2", "slave3"]:
        bin_files_path, idxs_path = get_data_files_path(input_dir, device_name)
        data_idx = get_data_idx(idxs_path, offset_time, frame_periodicity)
        print(data_idx)
        mmw_array = turn_device_frame(bin_files_path, adc_samples_num, chrips_num, bracket_idx, data_idx, x_sample_num)
        np.save(input_dir / f"{device_name}_mmw_array.npy", mmw_array)

#    print(get_idx_info(input_dir / "slave1_0000_idx.bin"))
