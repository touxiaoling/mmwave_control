from datetime import timedelta, datetime
from pathlib import Path

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
    timestamps = np.array([log[-2] for log in data])
    return header[3], header[4], timestamps


def load(inputdir: Path, device: str):
    """Load the recordings of the radar chip provided in argument.

    Arguments:
        inputdir: Input directory to read the recordings from
        device: Name of the device

    Return:
        Dictionary containing the data and index files
    """
    inputdir = Path(inputdir)
    recordings = {
        "data": sorted(inputdir.glob(f"{device}*_data.bin")),
        "idx": sorted(inputdir.glob(f"{device}*_idx.bin")),
    }
    if len(recordings["data"]) == 0 or len(recordings["idx"]) == 0:
        raise FileNotFoundError(f"No data or index files found for {device} in the input directory")
    elif len(recordings["data"]) != len(recordings["idx"]):
        print(
            f"[ERROR]: Missing {device} data or index file!\n"
            "Please check your recordings!"
            "\nYou must have the same number of "
            "'*data.bin' and '*.idx.bin' files."
        )
        raise ValueError("Number of data and index files do not match")
    return recordings


def toframe(mf: Path, sf0: Path, sf1: Path, sf2: Path, ns: int, nc: int, nf: int, output: str = ".", start_idx: int = 0):
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
    nwave = 2
    nchip = 4
    ntx = 3
    nrx = 4
    nf_skip = 0
    fk = start_idx

    nitems = nwave * ns * nc * nrx * ntx * nchip

    def load_dev(dev_file: Path, offset: int):
        dev = np.fromfile(dev_file, dtype=np.int16, count=nitems, offset=offset)
        dev = dev.reshape(nc, ntx * nchip, ns, nrx, 2)
        dev = np.transpose(dev, (1, 3, 0, 2, 4))
        return dev

    for fidx in range(nf_skip, nf):
        offset = fidx * nitems * 2

        dev1 = load_dev(mf, offset)
        dev2 = load_dev(sf0, offset)
        dev3 = load_dev(sf1, offset)
        dev4 = load_dev(sf2, offset)

        frame = np.zeros((nchip * ntx, nrx * nchip, nc, ns, 2))
        print(frame.shape)
        frame[:, 0:4, :, :] = dev4
        frame[:, 4:8, :, :] = dev1
        frame[:, 8:12, :, :] = dev3
        frame[:, 12:16, :, :] = dev2

        # Name for saving the frame
        fpath = f"{output}/frame_{fk:04d}.npz"
        np.savez(fpath, frame)
        #frame.astype(np.int16).tofile(fpath)
        fk += 1

    # Return the index of the last frame generated
    return fk - 1


if __name__ == "__main__":
    from rich.console import Console
    import matplotlib.pyplot as plt
    from pathlib import Path
    from tqdm import tqdm
    print = Console().print
    output_dir = Path("../output")
    ns = 256  # number of ADC samples per chirp
    bc = 16  # number of chrips per frame
    input_dir = Path("../mmwave_data")
    master_idx = input_dir / "master_0001_idx.bin"
    info = get_bin_info(master_idx)
    print(info[0])
    print(info[1])


    frame_files = sorted(output_dir.glob("frame_*.npz"))
    frame_array = []
    for frame_file in tqdm(frame_files):
        frame:np.ndarray = np.load(frame_file)["arr_0"]
        frame_i = frame[0,0,:,:,0]
        frame_q = frame[0,0,:,:,1]
        frame_complex = np.zeros_like(frame_i, dtype=np.complex64)
        frame_complex.real = frame_i
        frame_complex.imag = frame_q
        for i in range(bc):
            frame_array.append(frame_complex[i])

    frame_array = np.array(frame_array)
    np.savez("../frame_array.npz", frame_array)

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
