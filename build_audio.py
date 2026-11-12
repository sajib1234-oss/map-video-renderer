import math
import os
import random
import shutil
import struct
import subprocess
import wave

PROJ = os.path.dirname(os.path.abspath(__file__))
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
SR = 44100
TOTAL_DUR = 36.10
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

# Procedural SFX Generators
# 1. Cinematic Air Whoosh (0.55s)
whoosh = []
n_w = int(0.55 * SR)
random.seed(101)
lp = 0.0
for i in range(n_w):
    t = i / SR
    env = math.sin(math.pi * (i / n_w)) ** 1.8
    cutoff = 0.05 + 0.28 * math.sin(math.pi * (i / n_w))
    white = random.uniform(-1, 1)
    lp = lp + cutoff * (white - lp)
    sub = 0.30 * math.sin(2 * math.pi * (100 - 50 * (t / 0.55)) * t)
    whoosh.append((lp * 0.85 + sub) * env * 0.45)

# 2. Crisp UI Pop (0.10s)
pop = []
n_p = int(0.10 * SR)
for i in range(n_p):
    t = i / SR
    env = math.exp(-t * 45)
    freq = 820 - 480 * (t / 0.10)
    pop.append((0.75 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2.0 * t)) * env * 0.50)

# 3. Deep Cinematic Bass Impact / Boom (0.80s)
boom = []
n_b = int(0.80 * SR)
for i in range(n_b):
    t = i / SR
    env = min(1.0, t / 0.005) * math.exp(-t * 4.5)
    freq = 68.0 * math.exp(-t * 2.5)
    sub = math.sin(2 * math.pi * freq * t)
    punch = math.sin(2 * math.pi * 140.0 * t) * math.exp(-t * 30.0)
    boom.append((sub * 0.80 + punch * 0.35) * env * 0.65)

# 4. Glass Chime / Bell (0.60s)
chime = []
n_c = int(0.60 * SR)
for i in range(n_c):
    t = i / SR
    env = min(1.0, t / 0.008) * math.exp(-t * 6.0)
    val = (0.50 * math.sin(2 * math.pi * 1046.50 * t) +
           0.32 * math.sin(2 * math.pi * 1567.98 * t) +
           0.18 * math.sin(2 * math.pi * 2093.00 * t))
    chime.append(val * env * 0.40)

# 5. Sonar Radar Ping / Coastline Wave (0.70s)
sonar = []
n_sn = int(0.70 * SR)
for i in range(n_sn):
    t = i / SR
    env = min(1.0, t / 0.015) * math.exp(-t * 4.2)
    carrier = math.sin(2 * math.pi * 1850 * t)
    mod = math.sin(2 * math.pi * 12 * t)
    sonar.append(carrier * (0.8 + 0.2 * mod) * env * 0.35)

# Decode voiceover to temporary 44.1kHz mono WAV
voice_mp3 = os.path.join(PROJ, "voiceover.mp3")
voice_wav = os.path.join(PROJ, "voiceover_temp.wav")
print(f"Decoding voiceover {voice_mp3} with ffmpeg ({FFMPEG})...")
subprocess.run([FFMPEG, "-y", "-i", voice_mp3, "-ar", "44100", "-ac", "1", voice_wav], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

vo_samples = read_wav(voice_wav)

# Create master buffer
master = [0.0] * TOTAL_SAMPLES

# Place voiceover with clarity boost
for i, s in enumerate(vo_samples):
    if i < TOTAL_SAMPLES:
        master[i] += s * 1.30

def overlay_sfx(sfx_arr, start_sec, vol=1.0):
    start_idx = int(start_sec * SR)
    for i, s in enumerate(sfx_arr):
        idx = start_idx + i
        if 0 <= idx < TOTAL_SAMPLES:
            master[idx] += s * vol

# Timed SFX placement synced with speech
overlay_sfx(whoosh, 0.15, vol=0.8)     # Opening zoom
overlay_sfx(chime, 1.54, vol=0.7)      # "Alaska"
overlay_sfx(whoosh, 3.50, vol=0.85)    # Pan to Texas
overlay_sfx(pop, 4.80, vol=0.75)       # "Texas is huge"
overlay_sfx(boom, 6.66, vol=0.85)      # "makes it look surprisingly small"
overlay_sfx(chime, 8.64, vol=0.7)      # "Alaska is the largest state"
overlay_sfx(whoosh, 15.30, vol=0.8)    # "here's where things get crazy"
overlay_sfx(pop, 19.16, vol=0.8)       # "Texas"
overlay_sfx(pop, 20.06, vol=0.8)       # "California"
overlay_sfx(pop, 20.90, vol=0.8)       # "Montana"
overlay_sfx(boom, 21.30, vol=0.90)     # "combined!"
overlay_sfx(whoosh, 22.96, vol=0.8)    # "Imagine placing all three states"
overlay_sfx(chime, 27.26, vol=0.75)    # "still be larger"
overlay_sfx(sonar, 30.30, vol=0.85)    # "more coastline"
overlay_sfx(chime, 34.02, vol=0.7)     # "Did you think"

# Soft limiter
peak = max(abs(s) for s in master)
if peak > 0.98:
    scale = 0.98 / peak
    master = [s * scale for s in master]

master_wav = os.path.join(PROJ, "master_audio.wav")
write_wav(master_wav, master)

final_m4a = os.path.join(PROJ, "final_audio.m4a")
subprocess.run([FFMPEG, "-y", "-i", master_wav, "-c:a", "aac", "-b:a", "192k", final_m4a], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if os.path.exists(voice_wav):
    os.remove(voice_wav)
if os.path.exists(master_wav):
    os.remove(master_wav)

print(f"Master audio generated successfully: {final_m4a} ({os.path.getsize(final_m4a)} bytes)")
