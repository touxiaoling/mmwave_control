from datetime import timedelta, datetime
from pathlib import Path
from tqdm import tqdm,trange
import numpy as np


def get_bin_info(idx_file: Path):
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


def get_info(idx_file: Path):
    header, data = get_bin_info(idx_file)
    timestamps = np.asarray([log[-2] for log in data])
    return header[3], header[4], timestamps


def load_bin_info(inputdir: Path, device: str):
    """Load the recordings of the radar chip provided in argument.

    Arguments:
        inputdir: Input directory to read the recordings from
        device: Name of the device

    Return:
        Dictionary containing the data and index files
    """
    inputdir = Path(inputdir)
    data=sorted(inputdir.glob(f"{device}*_data.bin"))
    idx=sorted(inputdir.glob(f"{device}*_idx.bin"))
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
    return tuple(zip(data, idx))


def from_bin_file(bin_file: Path, frames_num: int, samples_num: int, chrips_num: int):
    """Re-Format the raw radar ADC recording.

    The raw recording from each device is merge together to create
    separate recording frames corresponding to the MIMO configuration.

    Arguments:
        mf: Path to the recording file of the master device
        sf0: Path to the recording file of the first slave device
        sf1: Path to the recording file of the second slave device
        sf2: Path to the recording file of the third slave device

        ns: Number of ADC samples per chirp
        nc: Number of chrips per frame
        nf: Number of frames to generate

        output: Path to the output folder where the frame files would
                be written

        start_idx: Index to start numbering the generated files from.

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

    final_res = None
    bin_file_array = np.fromfile(bin_file, dtype=np.int16)
    #print(bin_file_array.shape,frames_num*chrips_num,nitems,frames_num*nitems,bin_file_array.shape[0]/frames_num/nitems)
    #return bin_file_array
    for fidx in trange(frames_num):
        offset = fidx * nitems * 2

        dev = np.fromfile(bin_file, dtype=np.int16, count=nitems, offset=offset)
        dev = dev.reshape(chrips_num, ntx * devices_num, samples_num, nrx, nwave)
        dev = np.transpose(dev, (0, 1, 3, 2, 4))  # (chrips_num,ntx * nchip, nrx, samples_num, 2)
        dev_complex = np.zeros_like(dev[:,:,:,:,0], dtype=np.complex64)
        dev_complex.real = dev[:,:,:,:,0]
        dev_complex.imag = dev[:,:,:,:,1]

        #print(dev_complex.shape,dev_complex.dtype)
        if final_res is None:
            final_res = dev_complex
        else:
            final_res = np.concatenate((final_res,dev_complex), axis=0)
    # Return the index of the last frame generated
    return final_res


if __name__ == "__main__":
    from rich.console import Console
    import matplotlib.pyplot as plt

    print = Console().print
    samples_num = 256  # number of ADC samples per chirp
    chrips_num = 16  # number of chrips per frame
    #input_dir = Path("../outdoor_2024_11_11_19_44_00")
    input_dir = Path("../mmwave_data")
    master = load_bin_info(input_dir, "master")
    slave1 = load_bin_info(input_dir, "slave1")
    slave2 = load_bin_info(input_dir, "slave2")
    slave3 = load_bin_info(input_dir, "slave3")

    frame_files = input_dir / "master_frame.npz"
    time_stamp_files = input_dir / "timestamps.txt"

    all_frames = None
    all_times = None
    for bin_idx_file in master:
        bin_file=bin_idx_file[0]
        idx_file = bin_idx_file[1]
        print(bin_file,idx_file)
        frames_num, _, timelogs = get_info(idx_file)
        
        frame_array = from_bin_file(bin_file, frames_num, samples_num, chrips_num)
        if all_frames is None:
            all_frames = frame_array
            all_times = timelogs
        else:
            all_frames = np.concatenate((all_frames, frame_array), axis=0)
            all_times = np.concatenate((all_times, timelogs),axis=0)
    print(all_frames.shape,all_times.shape)
    #np.savez(frame_files, all_frames,all_times)

    # print(frame_1)

    # master = load(input_dir, "master")
    # slave1 = load(input_dir, "slave1")
    # slave2 = load(input_dir, "slave2")
    # slave3 = load(input_dir, "slave3")

    # size = len(master["data"])

    # nf = 0
    # previous_nf = 0
    # timestamps = np.array([])
    # for idx in range(size):
    #     print(f"Processing frame {idx}")
    #     mf = master["data"][idx]
    #     mf_idx = master["idx"][idx]
    #     sf0 = slave1["data"][idx]
    #     sf1 = slave2["data"][idx]
    #     sf2 = slave3["data"][idx]

    #     nf, _, timelogs = get_info(mf_idx)
    #     timestamps = np.append(timestamps, timelogs)

    #     previous_nf = toframe(mf, sf0, sf1, sf2, ns, bc, nf, output_dir, start_idx=previous_nf + 1)

    # print(f"[SUCCESS]: {previous_nf:04} frames written!")
    # timestamps.tofile(output_dir / "timestamps.txt", "\n")

    # print(f"[SUCCESS]: {previous_nf:04d} MIMO frames successfully generated!")
