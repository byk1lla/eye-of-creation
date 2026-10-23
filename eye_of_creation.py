"""
EYE OF CREATION — ASCII sinematik döngü (pygame + numpy)

GÖZ -> göz bebeğine dalış -> CREATION -> BIG BANG -> GALAXY -> BLACK HOLE -> tekrar GÖZ

Kurulum:  pip install pygame numpy
Çalıştır: python eye_of_creation.py

Kontroller:
  SPACE     duraklat / devam
  1-5       sahneye atla (EYE, CREATION, BIG BANG, GALAXY, BLACK HOLE)
  <- / ->   hız
  C         renk modu (COLOR / MATRIX / MONO)
  ESC       çıkış
"""
import base64
import io
import math
import os

import numpy as np
import pygame

# Ortam değişkenleriyle ayarlanabilir (video/ekran koruyucu render'ı için)
W = int(os.environ.get("EOC_W", 1280))
H = int(os.environ.get("EOC_H", 760))
UI = W / 1280                                   # arayüz ölçeği
CELL_W = max(4, round(7 * UI))
CELL_H = max(6, round(11 * UI))
SAVER = os.environ.get("EOC_SAVER") == "1"      # 1 ise alt kontrol çubuğu gizlenir
TOP = round(30 * UI)
BOT = 0 if SAVER else round(26 * UI)
CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
MODES = ["COLOR", "MATRIX", "MONO"]
STAGES = ["EYE", "CREATION", "BIG BANG", "GALAXY", "BLACK HOLE"]

# Zaman çizelgesi (saniye)
T_DIVE, T_CRE, T_BANG, T_GAL, T_BH, T_BHDIVE, T_RET, LOOP = 9, 12, 23, 31, 41, 48, 51, 55.0
STAGE_START = [0.0, T_CRE, T_BANG, T_GAL, T_BH]
Z_DIVE_END = 10.0   # göz bebeği ekranı doldurduğu zoom
Z_BH_END = 8.0      # kara delik gölgesi ekranı doldurduğu zoom
Z_RET = 3.0         # kara deliğin içinden görünen gözün zoom'u

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("EYE OF CREATION")
clock = pygame.time.Clock()
FONT_NAMES = "consolas,menlo,dejavusansmono,couriernew,monospace"
font = pygame.font.SysFont(FONT_NAMES, CELL_H, bold=True)
ui_font = pygame.font.SysFont(FONT_NAMES, round(14 * UI), bold=True)

COLS = W // CELL_W
ROWS = (H - TOP - BOT) // CELL_H
GW, GH = COLS * CELL_W, ROWS * CELL_H

# Normalize koordinatlar: v [-1, 1], u en-boy oranına göre
_xs = ((np.arange(COLS) + 0.5) * CELL_W - GW / 2) / (GH / 2)
_ys = ((np.arange(ROWS) + 0.5) * CELL_H - GH / 2) / (GH / 2)
U, V = np.meshgrid(_xs, _ys)


def build_atlas():
    masks = []
    for ch in CHARS:
        surf = pygame.Surface((CELL_W, CELL_H))
        surf.fill((0, 0, 0))
        g = font.render(ch, True, (255, 255, 255))
        surf.blit(g, ((CELL_W - g.get_width()) // 2, (CELL_H - g.get_height()) // 2))
        masks.append(pygame.surfarray.array3d(surf)[:, :, 0].T.astype(np.float32) / 255.0)
    return np.stack(masks)


ATLAS = build_atlas()
N_CHARS = len(CHARS)


# ---------------------------------------------------------------- yardımcılar
def C(r, g, b):
    return np.array([r, g, b], np.float32)


def mix(a, b, t):
    t = np.asarray(t, np.float32)[..., None]
    return a * (1 - t) + b * t


def ss(e0, e1, x):
    t = np.clip((np.asarray(x, np.float64) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def h2(x, y):
    return (np.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1.0


def vnoise(x, y):
    xi, yi = np.floor(x), np.floor(y)
    xf, yf = x - xi, y - yi
    sx, sy = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
    a, b = h2(xi, yi), h2(xi + 1, yi)
    c, d = h2(xi, yi + 1), h2(xi + 1, yi + 1)
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy


def fbm(x, y, octaves=4):
    s, amp, f, norm = 0.0, 0.5, 1.0, 0.0
    for i in range(octaves):
        s = s + amp * vnoise(x * f + i * 17.3, y * f - i * 9.1)
        norm += amp
        amp *= 0.5
        f *= 2.03
    return s / norm


def stars(u, v, t, dens=0.012, sc=38.0):
    gx, gy = np.floor(u * sc), np.floor(v * sc)
    h = h2(gx + 0.13, gy + 7.7)
    s = np.clip((h - (1 - dens)) / dens, 0, 1)
    b = s * (0.55 + 0.45 * np.sin(t * 3 + h * 900))
    return np.stack([b * 225, b * 225, b * 250], -1).astype(np.float32)


def hot(I):
    I = np.clip(I, 0, 1.5)
    return np.stack([
        np.clip(I * 1.3, 0, 1) * 255,
        np.clip(I ** 1.5, 0, 1) * 215,
        np.clip(I ** 3, 0, 1) * 175,
    ], -1).astype(np.float32)


# ---------------------------------------------------------------- GÖZ
def eye_scene(u, v, t, z=1.0, ix=0.0, iy=0.0, openness=1.0,
              portal=None, portal_k=1.0, portal_amt=0.0):
    ue, ve = u / z, v / z
    n = fbm(ue * 2.5 + 3, ve * 4)
    n2 = fbm(ue * 9, ve * 14, 3)
    col = C(128, 80, 52) * (0.45 + 0.35 * n + 0.15 * n2)[..., None]

    a = 1.75
    k = np.clip(1 - (ue / a) ** 2, 0, None)
    up, dn = -0.82 * openness * k, 0.62 * openness * k
    inside = (np.abs(ue) < a) & (ve > up) & (ve < dn)

    fold = np.exp(-((ve - (up - 0.3 * k - 0.02)) ** 2) / 0.003) * (np.abs(ue) < a * 1.05)
    fold2 = np.exp(-((ve - (dn + 0.12 * k + 0.02)) ** 2) / 0.004) * (np.abs(ue) < a)
    col = col * (1 - 0.5 * fold - 0.3 * fold2)[..., None]

    # akı
    edge = np.clip(np.abs(ue) / a, 0, 1)
    lidsh = np.clip((ve - up) / 0.3, 0, 1)
    sclera = C(246, 242, 236) * ((1 - 0.35 * edge ** 3) * (0.55 + 0.45 * lidsh))[..., None]
    sclera = mix(sclera, C(200, 118, 108), np.clip((-ue / a - 0.75) * 4, 0, 1) * 0.7)
    col = np.where(inside[..., None], sclera, col)

    # iris
    ri = 0.56
    du, dv = ue - ix, ve - iy
    d = np.hypot(du, dv)
    ang = np.arctan2(dv, du)
    kk = np.clip(d / ri, 0, 1)
    streak = 0.5 + 0.5 * np.sin(ang * 55 + 4 * np.sin(ang * 9) + kk * 8)
    iris = mix(C(228, 192, 48), C(30, 155, 110), ss(0.35, 0.7, kk))
    iris = mix(iris, C(12, 70, 55), ss(0.86, 0.98, kk))
    iris = iris * ((0.7 + 0.35 * streak) * (0.6 + 0.4 * lidsh))[..., None]
    col = np.where((inside & (d < ri))[..., None], iris, col)

    # göz bebeği (+ içindeki portal)
    rp = 0.22
    pup = C(22, 13, 9) * (0.6 + 0.8 * fbm(du * 8, dv * 8, 2))[..., None]
    if portal is not None and portal_amt > 0:
        pup = mix(pup, portal(du * portal_k, dv * portal_k), portal_amt)
    col = np.where((inside & (d < rp))[..., None], pup, col)

    # parlama
    hd = np.hypot(ue - (ix - 0.2), (ve - (iy - 0.2)) * 1.1)
    hl = np.clip(1 - hd / 0.12, 0, 1) ** 0.5 * (1 - portal_amt)
    col = np.where(inside[..., None], mix(col, C(255, 255, 252), hl * 0.95), col)

    lash = (np.abs(ve - up) < 0.03 * (0.5 + k)) & (np.abs(ue) < a)
    col = np.where(lash[..., None], C(28, 16, 10), col)
    return col


# ---------------------------------------------------------------- CREATION
# Michelangelo - "Adem'in Yaratılışı" (Sistina Şapeli, kamu malı).
# Eller kırpılıp duvar arka planı siyaha çekilmiş hali, JPEG olarak gömülü.
HANDS_JPG = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwMDAgQDAwMEBAQFBgoGBgUFBgwICQcKDgwPDg4MDQ0PERYTDxAVEQ0NExoTFRcY"
    "GRkZDxIbHRsYHRYYGRj/2wBDAQQEBAYFBgsGBgsYEA0QGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgY"
    "GBgYGBgYGBj/wAARCAGRA3ADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUF"
    "BAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVW"
    "V1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi"
    "4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAEC"
    "AxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVm"
    "Z2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq"
    "8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8/wCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACi"
    "iigAr0z4OXmk6R4nbWNSlVWgGY1Y4ye1eZ05JHT7jlfoamUeZWGnZ3O8+KvjWfxh4wmuZJvOAbG/sfYDsPauBoJJOTRRGKirIG76"
    "hRRRVCCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigDqdD8e65oOkS6dZXLpDIMMoOAa5q4ne5uXnkOWc5J"
    "qOikklqFwooopgFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFdX4"
    "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"
    "jJ963g+WIJXM69dwsjtgDnGTnk+orynxff8A+ktGGbaoJOOoJ6fjXomt3hSzYyvkY3EDjJ+leN+KLvDS7mbcQxP+ArmrVXsI4bUJ"
    "hsA8zPH+c1hzMfLkOzf8hIzk9qt6hK0t4QSdu7PtWdqM6QaZIzNszwCRmopJ3SMKj3Or0y4tk0mAxOVkWAIySLgls9en/wCsVfWd"
    "o1PmRbiP41+bHviuL0nV5Lqx3zvb7SeFTqPXcM/p9K0v7WSKJk+z7toyWTOMenH5V6bpyTPBqUOqOh/tKyiKgyNHng8YJ/OlGsRL"
    "e7Y5VABxtcY7dv8A9dc5FqisgEud3JIIOAfTGPSlDWt1MxVjtVhgZKjPOBnoM1DiYujJandJfrLbZlCqzjscg96lMu6FCqbju5KH"
    "BA+hNYFvJKsUZKsApweAMe4qR9TNtA0gkXavTzFBxz+lKULkpyvY31y7FkO5c84OP89qWdHhCylQAxCHJ5X0/wAKz7TV4/IHnwgA"
    "DJYnHP0PX61PNqNpLCI7e5CyM2dpI5AIJPP0rJwsaqbXQcI4zO0hJdkcgfN06dMVE0SrcNLtKblCtIR1wTgfhk1K00mN8UaMNpbJ"
    "OC2D14yB3qBJYlXzRFkk8qX3tn0xUWsXzX0Y9JCro6E7wpBdTg++T1rJ1O2/ta4xOqrCefmT5pAPXsOPbNaqr50Z85j8g6Dj5jz+"
    "Q4FMkSZ7k7IgIh1ZzjcO/wDnFPVSuhwk4nj3xC+FOmeIoPP0y3FvOCwKkBQe/B6YwePXNeU3nwJ1yKyea2YyMqhijDBGelfVF3Hc"
    "RStLCVdZCF25BG4HB9QflI49jSPYI0RkV/LPB9Q31H4130syqQSjI6ZU431Pg/V/D2qaLcNFe2sibTjJU1V02/m03UoruFirI2ci"
    "vtTxD4N0nxPZzW95bIsqjakifNnA7+vGOR+tfLfjr4d6n4Z1KSRLdmtSSUcDIIr2MNjIV1puZ1KLhr0PZfBnxe0eXSo47+URzqvL"
    "N06c1d1+78O+P/DlxDDcjMeWAZv69/6V8qBnQkBiprR03WNSsGZbS5ePd15rtUtLM5XTV7olu2n8PeIZUsbggxtgMp61tRfErxJG"
    "oBvJDtGBzXJXEkktw0krbmJyTUVSXYv6rq11q96bm7fc571QoooGFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAfQn7K3hmTUfiKNVl"
    "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"
)


def _load_hands():
    raw = base64.b64decode("".join(HANDS_JPG))
    surf = pygame.image.load(io.BytesIO(raw), "hands.jpg")
    return pygame.surfarray.array3d(surf).transpose(1, 0, 2).astype(np.float32)


HANDS = _load_hands()
HANDS_PX = HANDS.shape[1] / 4.6  # piksel / birim (görsel 4.6 birim genişliğinde)


def sample_hands(x, y):
    """Görseli birim koordinatlarından bilinear örnekle (dışarısı siyah)."""
    h, w = HANDS.shape[:2]
    px = x * HANDS_PX + w / 2 - 0.5
    py = y * HANDS_PX + h / 2 - 0.5
    valid = (px >= 0) & (px < w - 1) & (py >= 0) & (py < h - 1)
    px = np.clip(px, 0, w - 1.001)
    py = np.clip(py, 0, h - 1.001)
    x0, y0 = px.astype(np.int32), py.astype(np.int32)
    fx, fy = (px - x0)[..., None], (py - y0)[..., None]
    c = (HANDS[y0, x0] * (1 - fx) * (1 - fy) + HANDS[y0, x0 + 1] * fx * (1 - fy)
         + HANDS[y0 + 1, x0] * (1 - fx) * fy + HANDS[y0 + 1, x0 + 1] * fx * fy)
    return c * valid[..., None]


def creation(u, v, lt):
    p = lt / (T_BANG - T_CRE)
    cz = 1 + 0.8 * ss(0, 1, p)                      # parmak uçlarına yavaş zoom
    uu = u / cz + 0.03 * math.sin(lt * 0.3)
    vv = v / cz + 0.02 * math.sin(lt * 0.23)
    off = 0.32 * (1 - ss(0, 0.7, p))                # eller birbirine yaklaşır

    left = sample_hands(uu + off, vv) * ((uu + off) < 0)[..., None]
    right = sample_hands(uu - off, vv) * ((uu - off) >= 0)[..., None]
    img = left + right

    lum = (0.3 * img[..., 0] + 0.59 * img[..., 1] + 0.11 * img[..., 2]) / 255
    gold = C(245, 192, 110) * (lum * 1.2)[..., None]
    body = np.clip(mix(img, gold, 0.4) * 1.35, 0, 255)

    col = stars(uu, vv, lt) * 0.8
    neb = fbm(uu * 1.5 - lt * 0.05, vv * 1.5)
    col = col + C(140, 95, 40) * (ss(0.6, 0.85, neb) * 0.18)[..., None]
    col = np.where((lum > 0.05)[..., None], body, col)

    # parmak uçları arasındaki kıvılcım -> beyaz patlama
    sd = np.hypot(uu, vv)
    flash = float(ss(0.82, 1.0, p))
    spark = np.exp(-(sd ** 2) / (0.0008 + 0.01 * ss(0.6, 0.85, p) + 6 * flash ** 2))
    spark = spark * (0.3 + 0.7 * ss(0.55, 0.8, p) + 0.15 * math.sin(lt * 9))
    col = col + C(255, 240, 210) * spark[..., None]
    return mix(col, C(255, 250, 240), flash ** 2)


# ---------------------------------------------------------------- BIG BANG
def bigbang(u, v, lt):
    p = lt / (T_GAL - T_BANG)
    r = np.hypot(u, v)
    a = np.arctan2(v, u)
    col = np.zeros(u.shape + (3,), np.float32)
    travel = 3.0 * (1 - math.exp(-lt / 2.0)) + 0.12 * lt
    fade = 1 - 0.85 * ss(0.6, 1.0, p)
    for layer, (nb, ln) in enumerate([(160, 0.25), (260, 0.12)]):
        bins = np.floor((a + math.pi) / (2 * math.pi) * nb)
        h = h2(bins + layer * 31, layer * 7.0 + 1)
        h3 = h2(bins * 1.7 + 3, layer + 11.0)
        ph = (h + travel * (0.4 + 0.6 * h3)) % 1.0
        pos = ph ** 2 * 2.4
        L = ln + 0.5 * ph * (1 - ss(0.3, 0.8, p))
        m = (r > pos) & (r < pos + L) & (h3 > 0.35)
        col = col + C(235, 240, 255) * ((0.3 + 0.7 * ph) * m * fade * (1 - 0.4 * layer))[..., None]
    glow = np.exp(-r * r * 12) * (0.6 * (1 - ss(0.2, 0.6, p)) + 0.3)
    cloud = fbm(u * 3 + lt * 0.05, v * 3 - lt * 0.03)
    cl = ss(0.35, 0.9, p) * np.exp(-r * r * 1.3) * ss(0.35, 0.85, cloud)
    col = col + C(200, 205, 220) * (cl * 0.9)[..., None] + C(255, 250, 240) * glow[..., None]
    col = col + stars(u, v, lt) * float(ss(0.5, 1, p))
    return mix(col, C(255, 255, 255), float(1 - ss(0, 0.9, lt)))


# ---------------------------------------------------------------- GALAXY
def galaxy(u, v, lt):
    p = lt / (T_BH - T_GAL)
    gz = 0.9 + 0.9 * ss(0, 1, p)
    uu, vv = u / gz, v / gz
    tl = -0.35
    x = uu * math.cos(tl) - vv * math.sin(tl)
    y = (uu * math.sin(tl) + vv * math.cos(tl)) / 0.5
    r = np.hypot(x, y) + 1e-4
    th = np.arctan2(y, x)
    rot = lt * 0.18
    arm = np.cos(2 * (th - rot) - np.log(r) * 3.2)
    armk = float(ss(0, 0.3, p))
    n = fbm(x * 4 + rot, y * 4)
    dens = np.exp(-r * 1.6) * (0.35 + armk * 1.3 * np.clip(arm, 0, 1) ** 2 * (0.6 + 0.8 * n) + (1 - armk) * n)
    core = np.exp(-r * r * 25)
    col = stars(u * 0.8 / gz, v * 0.8 / gz, lt)
    col = col + C(80, 120, 235) * np.clip(dens * 1.6, 0, 1.2)[..., None]
    col = col + C(170, 190, 255) * (np.exp(-r * r * 4) * 0.25)[..., None]
    return col + C(255, 240, 215) * (core * 1.1)[..., None]


# ---------------------------------------------------------------- BLACK HOLE
def blackhole(u, v, lt, zb=1.0, portal=None, portal_amt=0.0):
    uu, vv = u / zb, v / zb
    tl = -0.12
    x = uu * math.cos(tl) - vv * math.sin(tl)
    y = uu * math.sin(tl) + vv * math.cos(tl)
    r = np.hypot(x, y)
    rs = 0.3
    col = stars(uu * 1.3, vv * 1.3, lt) * 0.9

    ye = y / 0.2
    re = np.hypot(x, ye)
    th = np.arctan2(ye, x)
    I = np.clip(np.exp(-(re - 0.42) * 1.5), 0, 1) * (re > 0.38) * (re < 2.2)
    I = I * (0.65 + 0.35 * np.sin(th * 7 - lt * 2.5 + re * 14))
    I = np.clip(I * (1 + 0.45 * (-x / (re + 1e-3))), 0, 1.3)
    disk = hot(I)

    ring = np.exp(-((r - 0.335) / 0.022) ** 2) * 1.2 + np.exp(-((r - 0.40) / 0.07) ** 2) * 0.6
    col = col + disk * (y < 0)[..., None] + hot(np.clip(ring, 0, 1.4))

    shadow = np.zeros_like(col)
    if portal is not None and portal_amt > 0:
        shadow = mix(shadow, portal(uu * Z_BH_END, vv * Z_BH_END), portal_amt)
    col = np.where((r < rs)[..., None], shadow, col)
    return col + disk * (y >= 0)[..., None] * (1 - portal_amt)


# ---------------------------------------------------------------- zaman çizelgesi
def blink(t, times, dur=0.28):
    for bt in times:
        p = (t - bt) / dur
        if 0 <= p <= 1:
            return max(0.04, abs(1 - 2 * p))
    return 1.0


def frame(T):
    """Döngü zamanına göre (renk ızgarası, sahne no, zoom üssü) döner."""
    t = T % LOOP
    u, v = U, V
    if t < T_DIVE:
        g = 1 - ss(7.5, 9.0, t)
        col = eye_scene(u, v, t, z=1 + 0.15 * ss(0, 9, t),
                        ix=0.28 * math.sin(t * 0.6) * g, iy=0.08 * math.sin(t * 0.9) * g,
                        openness=blink(t, (2.8, 6.2)))
        stage = 0
    elif t < T_CRE:
        s = (t - T_DIVE) / (T_CRE - T_DIVE)
        z = 1.15 * (Z_DIVE_END / 1.15) ** (s * s)
        col = eye_scene(u, v, t, z=z, portal=lambda pu, pv: creation(pu, pv, 0.0),
                        portal_k=Z_DIVE_END, portal_amt=float(ss(0.1, 0.7, s)))
        stage = 0
    elif t < T_BANG:
        col, stage = creation(u, v, t - T_CRE), 1
    elif t < T_GAL:
        col, stage = bigbang(u, v, t - T_BANG), 2
    elif t < T_BH:
        lt = t - T_GAL
        col = galaxy(u, v, lt)
        if lt < 1.5:
            col = mix(bigbang(u, v, T_GAL - T_BANG), col, float(ss(0, 1.5, lt)))
        stage = 3
    elif t < T_RET:
        lt = t - T_BH
        if t < T_BHDIVE:
            zb, pamt, portal = 1 + 0.25 * ss(0, 7, lt), 0.0, None
        else:
            s = (t - T_BHDIVE) / (T_RET - T_BHDIVE)
            zb = 1.25 * (Z_BH_END / 1.25) ** (s * s)
            pamt = float(ss(0.2, 0.8, s))
            portal = lambda pu, pv: eye_scene(pu, pv, t, z=Z_RET)
        col = blackhole(u, v, lt, float(zb), portal, pamt)
        if lt < 1.5:
            col = mix(galaxy(u, v, T_BH - T_GAL), col, float(ss(0, 1.5, lt)))
        stage = 4
    else:
        s = (t - T_RET) / (LOOP - T_RET)
        e = 1 - (1 - s) ** 2
        col, stage = eye_scene(u, v, t, z=Z_RET ** (1 - e)), 0

    zexp = t * 0.62 if t < T_RET else T_RET * 0.62 * (1 - (t - T_RET) / (LOOP - T_RET))
    return np.clip(col, 0, 255), stage, zexp


# ---------------------------------------------------------------- ASCII render
def to_ascii_surface(col, mode):
    lum = (0.30 * col[..., 0] + 0.59 * col[..., 1] + 0.11 * col[..., 2]) / 255.0
    idx = np.clip((lum ** 0.75) * (N_CHARS - 1), 0, N_CHARS - 1).astype(np.int32)
    idx[lum < 0.045] = 0  # karanlık bölgeler boş kalsın, karakter gürültüsü olmasın
    if mode == "MATRIX":
        col = np.stack([lum * 60, lum * 255, lum * 90], -1)
    elif mode == "MONO":
        col = np.stack([lum * 255] * 3, -1)
    col = np.clip(col * 1.15, 0, 255).astype(np.float32)
    img = (0.32 + 0.68 * ATLAS[idx][..., None]) * col[:, :, None, None, :]
    img = img.transpose(0, 2, 1, 3, 4).reshape(GH, GW, 3)
    img[::3] *= 0.72  # CRT scanline
    return pygame.surfarray.make_surface(np.clip(img, 0, 255).transpose(1, 0, 2).astype(np.uint8))


def draw_text(s, pos, color):
    surf = ui_font.render(s, True, color)
    screen.blit(surf, pos)
    return surf.get_width()


def draw_header(stage):
    x = round(16 * UI)
    for i, name in enumerate(STAGES):
        if i == stage:
            x += draw_text("> " + name, (x, round(8 * UI)), (255, 205, 90))
        else:
            x += draw_text(name, (x, round(8 * UI)), (105, 105, 110))
        x += round(26 * UI)


def main():
    T, speed, paused, mode_i = 0.0, 1.0, False, 0
    last = pygame.time.get_ticks()
    while True:
        now = pygame.time.get_ticks()
        dt = (now - last) / 1000
        last = now
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_c:
                    mode_i = (mode_i + 1) % len(MODES)
                elif e.key == pygame.K_RIGHT:
                    speed = min(4.0, speed + 0.25)
                elif e.key == pygame.K_LEFT:
                    speed = max(0.25, speed - 0.25)
                elif pygame.K_1 <= e.key <= pygame.K_5:
                    T = STAGE_START[e.key - pygame.K_1]
        if not paused:
            T += min(dt, 0.1) * speed

        col, stage, zexp = frame(T)
        surf = to_ascii_surface(col, MODES[mode_i])

        screen.fill((6, 6, 8))
        screen.blit(surf, ((W - GW) // 2, TOP))
        draw_header(stage)
        if not SAVER:
            draw_text(
                f"ZOOM x10^{zexp:4.1f}   {STAGES[stage]}   {clock.get_fps():.0f} fps   speed {speed:.2f}   "
                "[SPACE] duraklat  [1-5] sahne  [<-/->] hız  [C] mod  [ESC] çık",
                (round(16 * UI), H - BOT + round(5 * UI)), (150, 150, 150),
            )
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
