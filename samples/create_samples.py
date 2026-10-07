import os
import math
import wave
import struct
import numpy as np

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))

def save_wav(filename: str, sample_rate: int, samples: np.ndarray):
    filepath = os.path.join(SAMPLES_DIR, filename)
    # Normalize to 16-bit integer
    samples = samples / (np.max(np.abs(samples)) + 1e-9)
    int_samples = (samples * 32767 * 0.9).astype(np.int16)
    
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    print(f"Generated {filepath} ({len(int_samples)/sample_rate:.2f}s)")

def make_chickadee():
    sr = 22050
    t = np.linspace(0, 2.5, int(sr * 2.5), endpoint=False)
    sig = np.zeros_like(t)

    # Note 1: "Fee" ~ 3450 Hz (0.2s - 0.6s)
    idx1 = (t >= 0.2) & (t <= 0.6)
    env1 = np.hanning(np.sum(idx1))
    sig[idx1] += env1 * np.sin(2 * np.pi * 3450 * t[idx1])

    # Note 2: "Bee" ~ 3100 Hz (0.75s - 1.25s) with slight down-slur
    idx2 = (t >= 0.75) & (t <= 1.25)
    env2 = np.hanning(np.sum(idx2))
    f2 = np.linspace(3150, 3050, np.sum(idx2))
    sig[idx2] += env2 * np.sin(2 * np.pi * f2 * t[idx2])

    # "Dee-dee" notes (1.5s - 2.2s)
    for start in [1.5, 1.7, 1.9, 2.1]:
        idx = (t >= start) & (t <= start + 0.12)
        if np.sum(idx) > 0:
            env = np.hanning(np.sum(idx))
            sig[idx] += 0.7 * env * (np.sin(2 * np.pi * 3800 * t[idx]) + 0.5 * np.sin(2 * np.pi * 7600 * t[idx]))

    save_wav("chickadee_call.wav", sr, sig)

def make_robin():
    sr = 22050
    t = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
    sig = np.zeros_like(t)

    # Melodic caroling syllables: cheerily, cheer-up, cheerily
    syllables = [
        (0.2, 0.45, 2200, 2600),
        (0.6, 0.90, 2800, 2400),
        (1.1, 1.40, 2300, 2900),
        (1.6, 1.95, 2700, 2200),
        (2.1, 2.45, 2400, 2800)
    ]
    for start, end, f_start, f_end in syllables:
        idx = (t >= start) & (t <= end)
        n = np.sum(idx)
        env = np.hanning(n)
        freqs = np.linspace(f_start, f_end, n)
        # Add slight vibrato
        vibrato = 15.0 * np.sin(2 * np.pi * 7 * t[idx])
        sig[idx] += env * (np.sin(2 * np.pi * (freqs + vibrato) * t[idx]) + 0.3 * np.sin(2 * np.pi * (freqs*2) * t[idx]))

    save_wav("american_robin.wav", sr, sig)

def make_cardinal():
    sr = 22050
    t = np.linspace(0, 2.8, int(sr * 2.8), endpoint=False)
    sig = np.zeros_like(t)

    # Rapid upward whoits and trills (2.2k -> 4.2k)
    sweeps = [
        (0.2, 0.55, 2100, 3900),
        (0.7, 1.05, 2200, 4100),
        (1.2, 1.55, 2300, 4200),
        (1.8, 2.50, 3200, 3300) # Fast trill
    ]
    for start, end, f0, f1 in sweeps:
        idx = (t >= start) & (t <= end)
        n = np.sum(idx)
        env = np.hanning(n)
        if f0 == 3200:
            # Trill
            pulse = 0.5 + 0.5 * np.sin(2 * np.pi * 18 * t[idx])
            sig[idx] += env * pulse * np.sin(2 * np.pi * 3250 * t[idx])
        else:
            freqs = np.linspace(f0, f1, n)
            sig[idx] += env * np.sin(2 * np.pi * freqs * t[idx])

    save_wav("northern_cardinal.wav", sr, sig)

def make_mourning_dove():
    sr = 22050
    t = np.linspace(0, 3.5, int(sr * 3.5), endpoint=False)
    sig = np.zeros_like(t)

    # Coo-OO-oo-oo-oo: initial soft coo, higher accent, three descending coos (450Hz - 580Hz)
    coos = [
        (0.3, 0.7, 460),
        (0.85, 1.4, 560), # accented higher
        (1.6, 2.0, 480),
        (2.1, 2.5, 460),
        (2.6, 3.0, 440)
    ]
    for start, end, freq in coos:
        idx = (t >= start) & (t <= end)
        n = np.sum(idx)
        env = np.hanning(n)
        sig[idx] += env * (np.sin(2 * np.pi * freq * t[idx]) + 0.25 * np.sin(2 * np.pi * (freq * 2) * t[idx]))

    save_wav("mourning_dove.wav", sr, sig)

def make_owl():
    sr = 22050
    t = np.linspace(0, 3.2, int(sr * 3.2), endpoint=False)
    sig = np.zeros_like(t)

    # Barred Owl / Great Horned Owl resonant hooting pattern (~320Hz)
    hoots = [
        (0.3, 0.65, 310),
        (0.8, 1.15, 320),
        (1.3, 1.60, 340),
        (1.8, 2.40, 290)
    ]
    for start, end, freq in hoots:
        idx = (t >= start) & (t <= end)
        n = np.sum(idx)
        env = np.hanning(n)
        sig[idx] += env * (np.sin(2 * np.pi * freq * t[idx]) + 0.2 * np.sin(2 * np.pi * (freq * 3) * t[idx]))

    save_wav("barred_owl.wav", sr, sig)

if __name__ == "__main__":
    make_chickadee()
    make_robin()
    make_cardinal()
    make_mourning_dove()
    make_owl()
    print("All bird call audio samples created successfully!")
