from . import schemas

#   - Max Range             : 80 m
#   - Range resolution      : 30 cm
#   - Max velocity          : 6.49 km/h
#   - Range resolution      : 0.4 km/h
default_cfg = dict(
    mimo=dict(
        profile=dict(
            id=0,
            startFrequency=77,  # GHz
            frequencySlope=15.0148,  # MHz/us
            idleTime=5,  # us
            adcStartTime=6,  # us
            rampEndTime=40,  # us
            numAdcSamples=256,  # ADC Samples per chirp
            rxGain=48,  # dB
        ),
        frame=dict(
            numFrames=0,  # Number of frames to record
            numLoops=16,  # Number of chirp loops per frame
            framePeriodicity=100,  # Frame periodicity in ms
        ),
        channel=dict(
            rxChannelEn=15,  # Enabled RX antenna bit field
            txChannelEn=7,  # Enabled TX Antenna bit field
        ),
    ),
)
default_cfg = schemas.MMWConfig.model_validate(default_cfg)

# Setup:
#   - Max Range: 15m
#   - Range resolution: 5cm
short_range_cfg = dict(
    mimo=dict(
        profile=dict(
            id=0,
            startFrequency=77,  # Start frequency in GHz
            frequencySlope=79.0327,  # Chrip slope in MHz/us
            idleTime=5,  # ADC idle time in us
            adcStartTime=6,  # ADC start time in us
            rampEndTime=40,  # Chrip ramp end time in us
            txStartTime=0,  # TX start time in us
            numAdcSamples=256,  # Number of ADC samples per chrip
            adcSamplingFrequency=8000,  # ADC sampling frequency in ksps
            rxGain=48,  # RX Gain in dB
            hpfCornerFreq1=0,  # High Pass Filter 1 corner frequency | 0: 175 kHz, 1: 235 kHz, 2: 350 kHz, 3: 700 kHz
            hpfCornerFreq2=0,  # High Pass Filter 2 corner frequency | 0: 350 kHz, 1: 700 kHz, 2: 1.4 MHz, 3: 2.8 MHz
        ),
        frame=dict(
            numFrames=0,  # Number of frames to record
            numLoops=16,  # Number of chirp loops per frame
            framePeriodicity=100,  # Frame periodicity in ms
        ),
        channel=dict(
            rxChannelEn=15,  # Enabled RX antenna bit field
            txChannelEn=7,  # Enabled TX Antenna bit field
        ),
    ),
)
short_range_cfg = schemas.MMWConfig.model_validate(short_range_cfg)
# Setup:
#   - Max Range: 9.26m
#   - Range resolution: ~5cm
very_short_range_cfg = dict(
    mimo=dict(
        profile=dict(
            id=0,
            startFrequency=77,  # Start frequency in GHz
            frequencySlope=48.57,  # Chrip slope in MHz/us
            idleTime=7,  # ADC idle time in us
            adcStartTime=6.4,  # ADC start time in us
            rampEndTime=69.07,  # Chrip ramp end time in us
            txStartTime=0,  # TX start time in us
            numAdcSamples=185,  # Number of ADC samples per chrip
            adcSamplingFrequency=3000,  # ADC sampling frequency in ksps
            rxGain=48,  # RX Gain in dB
            hpfCornerFreq1=0,  # High Pass Filter 1 corner frequency | 0: 175 kHz, 1: 235 kHz, 2: 350 kHz, 3: 700 kHz
            hpfCornerFreq2=0,  # High Pass Filter 2 corner frequency | 0: 350 kHz, 1: 700 kHz, 2: 1.4 MHz, 3: 2.8 MHz
        ),
        frame=dict(
            numFrames=0,  # Number of frames to record
            numLoops=16,  # Number of chirp loops per frame
            framePeriodicity=100,  # Frame periodicity in ms
        ),
        channel=dict(
            rxChannelEn=15,  # Enabled RX antenna bit field
            txChannelEn=7,  # Enabled TX Antenna bit field
        ),
    ),
)
very_short_range_cfg = schemas.MMWConfig.model_validate(short_range_cfg)
