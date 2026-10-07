import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.io.wavfile as wavfile
from typing import Dict, Any, Tuple

def analyze_audio_bytes(file_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes raw audio bytes (WAV format), extracts acoustic metrics,
    and produces a base64 encoded spectrogram.
    """
    try:
        buffer = io.BytesIO(file_bytes)
        sample_rate, data = wavfile.read(buffer)
    except Exception as e:
        # Fallback if raw PCM or unheadered
        raise ValueError(f"Could not decode audio file: {e}")

    # Convert to mono if stereo
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)

    # Normalize float data to -1.0 .. 1.0
    if np.issubdtype(data.dtype, np.integer):
        max_val = np.iinfo(data.dtype).max
        audio_norm = data.astype(np.float32) / max_val
    else:
        audio_norm = data.astype(np.float32)

    duration = float(len(audio_norm)) / float(sample_rate)
    rms_energy = float(np.sqrt(np.mean(audio_norm ** 2)))

    # Compute FFT
    n = len(audio_norm)
    if n == 0:
        raise ValueError("Audio is empty")

    fft_vals = np.abs(np.fft.rfft(audio_norm))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

    # Filter out sub-audible low rumble (<100Hz) and ultrasonic (>14000Hz)
    valid_mask = (freqs >= 100) & (freqs <= 14000)
    filtered_freqs = freqs[valid_mask]
    filtered_fft = fft_vals[valid_mask]

    if len(filtered_fft) > 0 and np.max(filtered_fft) > 0:
        peak_idx = np.argmax(filtered_fft)
        dominant_freq = float(filtered_freqs[peak_idx])

        # Spectral Centroid
        spectral_centroid = float(np.sum(filtered_freqs * filtered_fft) / (np.sum(filtered_fft) + 1e-12))

        # Bandwidth estimation (frequencies with amplitude > 25% of peak)
        threshold = 0.25 * filtered_fft[peak_idx]
        active_freqs = filtered_freqs[filtered_fft > threshold]
        freq_min = float(np.min(active_freqs)) if len(active_freqs) > 0 else dominant_freq
        freq_max = float(np.max(active_freqs)) if len(active_freqs) > 0 else dominant_freq
        bandwidth = freq_max - freq_min
    else:
        dominant_freq = 0.0
        spectral_centroid = 0.0
        freq_min = 0.0
        freq_max = 0.0
        bandwidth = 0.0

    # Classify pitch profile
    if dominant_freq < 700:
        pitch_profile = "Low-pitched / Resonant (Owl, Grouse, Large Raptor, Dove)"
    elif 700 <= dominant_freq < 2000:
        pitch_profile = "Mid-range Tonal (Crow, Jay, Woodpecker, Duck)"
    elif 2000 <= dominant_freq < 4500:
        pitch_profile = "Classic Songbird Whistle (Robin, Chickadee, Cardinal, Thrush)"
    else:
        pitch_profile = "High-frequency Warble / Trill (Warbler, Kinglet, Cedar Waxwing)"

    # Generate Spectrogram Image
    spectrogram_b64 = generate_spectrogram_image(audio_norm, sample_rate, dominant_freq)

    return {
        "sample_rate": sample_rate,
        "duration_seconds": round(duration, 2),
        "rms_energy": round(rms_energy, 4),
        "dominant_frequency_hz": round(dominant_freq, 1),
        "spectral_centroid_hz": round(spectral_centroid, 1),
        "frequency_range_hz": [round(freq_min, 1), round(freq_max, 1)],
        "bandwidth_hz": round(bandwidth, 1),
        "pitch_profile": pitch_profile,
        "spectrogram_image": spectrogram_b64
    }

def generate_spectrogram_image(audio_norm: np.ndarray, sample_rate: int, peak_hz: float) -> str:
    """
    Renders an aesthetic field-guide bioacoustics spectrogram and returns base64 PNG data.
    """
    fig, ax = plt.subplots(figsize=(7, 2.5), dpi=100)
    fig.patch.set_facecolor('#111827')
    ax.set_facecolor('#0f172a')

    # Spectrogram using Matplotlib's specgram
    NFFT = min(1024, len(audio_norm))
    noverlap = min(512, NFFT // 2)

    if len(audio_norm) > 256:
        Pxx, freqs, bins, im = ax.specgram(
            audio_norm,
            NFFT=NFFT,
            Fs=sample_rate,
            noverlap=noverlap,
            cmap='viridis',
            scale='dB'
        )
        ax.set_ylim(100, min(8000, sample_rate // 2))
        ax.axhline(peak_hz, color='#f59e0b', linestyle='--', linewidth=1.2, alpha=0.85, label=f'Peak {int(peak_hz)}Hz')
        ax.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=8)
    else:
        ax.text(0.5, 0.5, "Short Audio Sample", color="white", ha="center")

    ax.set_title("Bioacoustic Trail Spectrogram (Local FFT)", color='#e2e8f0', fontsize=10, pad=6)
    ax.set_xlabel("Time (seconds)", color='#94a3b8', fontsize=8)
    ax.set_ylabel("Frequency (Hz)", color='#94a3b8', fontsize=8)
    ax.tick_params(colors='#94a3b8', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#334155')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"
