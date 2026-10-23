"""
Döngüyü pencere açmadan MP4'e kaydeder (ffmpeg gerekir).

  python tools/record.py cikti.mp4                    # 1280x760, alt bar dahil
  EOC_W=1920 EOC_H=1200 EOC_SAVER=1 python tools/record.py assets/EyeOfCreation.mp4

Video tam olarak bir döngü (55 sn) sürer; başı ve sonu aynı kare olduğundan
loop'ta dikiş görünmez.
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

FPS = 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "eye_of_creation.mp4"
CRF = os.environ.get("EOC_CRF", "22")

frame = [0]
pygame.time.get_ticks = lambda: int(frame[0] * 1000 / FPS)


class FakeClock:
    def tick(self, *a):
        return 0

    def get_fps(self):
        return FPS


pygame.time.Clock = FakeClock

import eye_of_creation as E  # noqa: E402

TOTAL = int(round(E.LOOP * FPS))
ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{E.W}x{E.H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
     "-pix_fmt", "yuv420p", "-crf", CRF, "-preset", "medium",
     "-movflags", "+faststart", "-tag:v", "avc1", OUT],
    stdin=subprocess.PIPE,
)
orig_flip = pygame.display.flip


def flip():
    orig_flip()
    ff.stdin.write(pygame.image.tobytes(pygame.display.get_surface(), "RGB"))
    frame[0] += 1
    if frame[0] % FPS == 0:
        print(f"\r{frame[0] // FPS}/{int(E.LOOP)} sn", end="", flush=True)
    if frame[0] >= TOTAL:
        ff.stdin.close()
        ff.wait()
        print(f"\nTamam: {OUT}")
        raise SystemExit


pygame.display.flip = flip
E.main()
