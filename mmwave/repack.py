from datetime import timedelta, datetime
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


# def get_info(idx_file: Path):
#     header, data = get_bin_info(idx_file)
#     timestamps = np.asarray([log[-2] for log in data])
#     return header[3], header[4], timestamps


def get_bin_file_path(inputdir: Path, device: str):
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
    # elif len(data) != len(idx):
    #     print(
    #         f"[ERROR]: Missing {device} data or index file!\n"
    #         "Please check your recordings!"
    #         "\nYou must have the same number of "
    #         "'*data.bin' and '*.idx.bin' files."
    #     )
    # raise ValueError("Number of data and index files do not match")
    return data


def load_bin_file(bin_file: Path, samples_num: int, chrips_num: int):
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
    assert bin_file_array.shape[0] % nitems == 0

    res = bin_file_array.reshape(-1, nitems)
    res = res.reshape(-1, ntx * devices_num, samples_num, nrx, nwave)
    res = np.transpose(res, (0, 1, 3, 2, 4))  # (chrips_num,ntx * nchip, nrx, samples_num, 2)
    return res


@contextmanager
def temp_memmap(dtype, shape: tuple):
    with NamedTemporaryFile(suffix=".bin") as temp_file:
        temp_file_path = Path(temp_file.name)
        print(temp_file_path)
        temp_array = np.memmap(temp_file_path, dtype=dtype, mode="w+", shape=shape)
        del temp_array
        temp_array = np.memmap(temp_file_path, dtype=dtype, mode="c", shape=shape)
        yield temp_array
        del temp_array


@contextmanager
def turn_all_frame(input_dir: Path, samples_num: int, chrips_num: int):
    all_bin_files = []
    for i, device_name in enumerate(("slave3", "master", "slave2", "slave1")):
        all_bin_files.append([])
        for j, bin_file_path in enumerate(get_bin_file_path(input_dir, device_name)):
            bin_file = load_bin_file(bin_file_path, samples_num, chrips_num)
            all_bin_files[i].append(bin_file)

    frame_num = np.sum([bin_file.shape[0] for bin_file in all_bin_files[0]])

    newshape = [frame_num, *(bin_file.shape[1:])]
    newshape[2] *= 4

    with temp_memmap(np.int16, newshape) as all_frames:
        for ii in range(i + 1):
            frame_idx = 0
            for jj in range(j + 1):
                channel_shape: tuple = all_bin_files[ii][jj].shape
                frame_end = frame_idx + channel_shape[0]
                all_frames[frame_idx:frame_end, :, 4 * ii : 4 * (ii + 1)] = all_bin_files[ii][jj]

                frame_idx += channel_shape[0]

        yield all_frames


@contextmanager
def get_mimo_idx(all_frames: np.ndarray, time_info: np.ndarray, samples_time=40, samples_num=201):
    new_shape = (time_info.shape[0], samples_num, *(all_frames.shape[1:]))

    with temp_memmap(np.int16, new_shape) as mmw_array:
        for i in trange(time_info.shape[0]):
            start = int(time_info[i, 0] * 1000 / samples_time)
            end = start + samples_num
            # end = int(time_info[i,1]*1000/samples_time)
            mmw_array[i, :] = all_frames[start:end]
        yield mmw_array


if __name__ == "__main__":
    from rich.console import Console
    import matplotlib.pyplot as plt
    from tqdm import trange

    print = Console().print
    samples_num = 256  # number of ADC samples per chirp
    chrips_num = 1  # number of chrips per frame

    input_dir = Path("../outdoor_20241112_192215")
    time_info = np.loadtxt(input_dir / "timestamps.txt")

    with turn_all_frame(input_dir, samples_num, chrips_num) as all_frames:
        with get_mimo_idx(all_frames, time_info) as mmw_array:
            np.save(input_dir / "mmw_array.npy", mmw_array)
