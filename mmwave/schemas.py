from pydantic import BaseModel
from typing import Optional


class MimoProfile(BaseModel):
    id: int = 0
    startFrequency: int = 77
    frequencySlope: float = 79.0327
    idleTime: int = 5
    adcStartTime: int = 6
    rampEndTime: int = 40
    txStartTime: int = 0
    numAdcSamples: int = 256
    adcSamplingFrequency: int = 8000
    rxGain: int = 48
    hpfCornerFreq1: int = 0
    hpfCornerFreq2: int = 0


class MimoFrame(BaseModel):
    numFrames: int = 0
    numLoops: int = 4
    framePeriodicity: int = 25


class MimoChannel(BaseModel):
    rxChannelEn: int = 15
    txChannelEn: int = 7


class BracketProfile(BaseModel):
    dx: int = 1
    dy: int = 2
    row: int = 151
    col: int = 401
    timestamps: str = "timestamps.txt"
    offset_time: float = -0.920


class MimoConfig(BaseModel):
    profile: MimoProfile = MimoProfile()
    frame: MimoFrame = MimoFrame()
    channel: MimoChannel = MimoChannel()


class BracketConfig(BaseModel):
    profile: BracketProfile = BracketProfile()


class MMWConfig(BaseModel):
    mimo: MimoConfig = MimoConfig()
    bracket: BracketConfig = BracketConfig()
