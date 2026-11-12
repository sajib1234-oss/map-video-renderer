import math
import os
import random
import struct
import subprocess
import wave

PROJ = r"C:\Users\user\.gemini\antigravity\scratch\four-corners-map-short"
FFMPEG = r"C:\Users\user\.gemini\antigravity\scratch\bangla_toon\node_modules\@ffmpeg-installer\win32-x64\ffmpeg.exe"
SR = 44100
TOTAL_DUR = 36.30
TOTAL_SAMPLES = int(TOTAL_DUR * SR)

def write_wav(path, samples):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        clamped = [max(-32767, min(32767, int(s * 32767))) for s in samples]
        wf.writeframes(struct.pack("<" + "h" * len(clamped), *clamped))

def read_wav(path):
    with wave.open(path, "rb") as wf:
        n = wf.getnframes()
        raw = wf.readframes(n)
        int16s = struct.unpack("<" + "h" * n, raw)
        return [s / 32767.0 for s in int16s]

# 1. Cinematic Air Whoosh (0.60s)
whoosh = []
n_w = int(0.60 * SR)
random.seed(42)
lp = 0.0
for i in range(n_w):
    t = i / SR
    env = math.sin(math.pi * (i / n_w)) ** 1.8
    cutoff = 0.05 + 0.28 * math.sin(math.pi * (i / n_w))
    white = random.uniform(-1, 1)
    lp = lp + cutoff * (white - lp)
    sub = 0.32 * math.sin(2 * math.pi * (110 - 55 * (t / 0.60)) * t)
    whoosh.append((lp * 0.85 + sub) * env * 0.45)

# 2. Crisp UI Pop (0.12s)
pop = []
n_p = int(0.12 * SR)
for i in range(n_p):
    t = i / SR
    env = math.exp(-t * 42)
    freq = 780 - 450 * (t / 0.12)
    pop.append((0.75 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2.0 * t)) * env * 0.55)

# 3. Soft UI Tick (0.08s)
tick = []
n_tk = int(0.08 * SR)
for i in range(n_tk):
    t = i / SR
    env = math.exp(-t * 60)
    freq = 1100 - 600 * (t / 0.08)
    tick.append(math.sin(2 * math.pi * freq * t) * env * 0.40)

# 4. Glass Chime / Monument Bell (0.65s)
chime = []
n_c = int(0.65 * SR)
for i in range(n_c):
    t = i / SR
    env = min(1.0, t / 0.008) * math.exp(-t * 5.8)
    val = (0.50 * math.sin(2 * math.pi * 987.77 * t) +
           0.32 * math.sin(2 * math.pi * 1479.98 * t) +
           0.18 * math.sin(2 * math.pi * 1975.53 * t))
    chime.append(val * env * 0.42)

# 5. Lock In / Target Shimmer (0.35s)
target_lock = []
n_tl = int(0.35 * SR)
for i in range(n_tl):
    t = i / SR
    env = min(1.0, t / 0.01) * math.exp(-t * 11)
    val = (0.6 * math.sin(2 * math.pi * 1200 * t) + 0.4 * math.sin(2 * math.pi * 1800 * t))
    target_lock.append(val * env * 0.45)

# Decode voiceover to temporary 44.1kHz mono WAV
voice_mp3 = os.path.join(PROJ, "voiceover.mp3")
voice_wav = os.path.join(PROJ, "voiceover_temp.wav")
subprocess.run([FFMPEG, "-y", "-i", voice_mp3, "-ar", "44100", "-ac", "1", voice_wav], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

vo_samples = read_wav(voice_wav)

# Create master buffer
master = [0.0] * TOTAL_SAMPLES

# Place voiceover with boost
for i, s in enumerate(vo_samples):
    if i < TOTAL_SAMPLES:
        master[i] += s * 1.35

def overlay_sfx(sfx_arr, start_sec, vol=1.0):
    start_idx = int(start_sec * SR)
    for i, s in enumerate(sfx_arr):
        idx = start_idx + i
        if 0 <= idx < TOTAL_SAMPLES:
            master[idx] += s * vol

# Add SFX strictly aligned with speech beats (NO BGM!)
# 1. Whoosh sounds
for t in [0.20, 7.80, 15.10, 21.90, 32.90]:
    overlay_sfx(whoosh, t, 0.40)

# 2. Pops on key reveals & state mentions
overlay_sfx(pop, 2.30, 0.55)   # "four different US states"
overlay_sfx(pop, 16.68, 0.60)  # "Arizona"
overlay_sfx(pop, 17.50, 0.60)  # "Utah"
overlay_sfx(pop, 18.02, 0.60)  # "Colorado"
overlay_sfx(pop, 18.82, 0.60)  # "New Mexico"
overlay_sfx(pop, 33.60, 0.55)  # "which state"

# 3. Ticks
overlay_sfx(tick, 6.20, 0.45)   # "impossible, right?"
overlay_sfx(tick, 15.50, 0.45)  # "Look at this map"
overlay_sfx(tick, 26.50, 0.45)  # "four state borders"

# 4. Monument & center chime / locks
overlay_sfx(chime, 11.80, 0.50) # "Four Corners Monument"
overlay_sfx(target_lock, 20.50, 0.55) # "one single point"
overlay_sfx(chime, 28.80, 0.55) # "marker on the ground"

# Soft limiter
for i in range(TOTAL_SAMPLES):
    v = master[i]
    if v > 0.95:
        master[i] = 0.95 + 0.05 * math.tanh((v - 0.95) / 0.05)
    elif v < -0.95:
        master[i] = -0.95 + 0.05 * math.tanh((v + 0.95) / 0.05)

mixed_wav = os.path.join(PROJ, "mixed_master.wav")
write_wav(mixed_wav, master)

final_m4a = os.path.join(PROJ, "final_audio.m4a")
subprocess.run([
    FFMPEG, "-y",
    "-i", mixed_wav,
    "-c:a", "aac",
    "-b:a", "192k",
    "-t", "36.30",
    final_m4a
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if os.path.exists(voice_wav):
    os.remove(voice_wav)
if os.path.exists(mixed_wav):
    os.remove(mixed_wav)

print(f"Successfully generated clean voiceover + SFX audio (NO BGM): {final_m4a} ({os.path.getsize(final_m4a)} bytes)")
