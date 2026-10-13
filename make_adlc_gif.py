"""Render a YMCA-style dance GIF: a costumed troupe spells A, D, L, C together."""
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 480
SS = 2  # supersampling factor
OUT = "adlc-dance.gif"
PREVIEW_DIR = os.environ.get("PREVIEW_DIR")  # optional: dump one still per letter

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Pose angles are math-style degrees (0 = screen right, 90 = up).
# arms: (right upper, right fore, left upper, left fore); legs: (R thigh, R shin, L thigh, L shin)
POSES = {
    "A": dict(arms=(72, 120, 108, 60), legs=(-68, -68, -112, -112), lean=0),
    "D": dict(arms=(35, -72, 90, 90), legs=(-80, -88, -100, -92), lean=0),
    "L": dict(arms=(92, 92, 88, 88), legs=(0, 0, -90, -90), lean=0),
    "C": dict(arms=(112, 178, 212, 305), legs=(-78, -86, -102, -94), lean=-8),
}
ORDER = "ADLC"

BG_TOP, BG_BOT = (44, 16, 92), (214, 54, 140)
EDGE = (40, 16, 50)

# The troupe: classic costume archetypes, drawn as cartoons.
CAST = [
    dict(role="cop", skin=(236, 190, 150), shirt=(34, 52, 120), sleeve_skin=False,
         pants=(24, 36, 90), shoes=(20, 20, 24), hat="cop", stache=True, shades=True),
    dict(role="construction", skin=(190, 130, 92), shirt=(60, 110, 190), sleeve_skin=True,
         pants=(60, 80, 130), shoes=(120, 80, 40), hat="hardhat", stache=True, vest=(255, 140, 20)),
    dict(role="cowboy", skin=(240, 200, 160), shirt=(230, 230, 220), sleeve_skin=False,
         pants=(70, 100, 170), shoes=(110, 60, 30), hat="cowboy", stache=False, vest=(130, 80, 40),
         bandana=(210, 40, 40)),
    dict(role="biker", skin=(150, 100, 70), shirt=(25, 25, 28), sleeve_skin=True,
         pants=(25, 25, 28), shoes=(15, 15, 15), hat="biker", stache=True, shades=True, vest=(10, 10, 12)),
    dict(role="sailor", skin=(230, 180, 140), shirt=(245, 245, 250), sleeve_skin=False,
         pants=(245, 245, 250), shoes=(30, 30, 50), hat="sailor", stache=False, collar=(30, 50, 120)),
]
SCALE = 0.8
SPACING = 126


def lerp(a, b, t):
    return a + (b - a) * t


def alerp(a, b, t):
    d = (b - a + 180) % 360 - 180
    return a + d * t


def ease(t):
    return t * t * (3 - 2 * t)


def pose_mix(p, q, t):
    t = ease(t)
    return dict(
        arms=tuple(alerp(a, b, t) for a, b in zip(p["arms"], q["arms"])),
        legs=tuple(alerp(a, b, t) for a, b in zip(p["legs"], q["legs"])),
        lean=lerp(p["lean"], q["lean"], t),
    )


def seg(origin, angle, length):
    r = math.radians(angle)
    return (origin[0] + length * math.cos(r), origin[1] - length * math.sin(r))


def font(size):
    return ImageFont.truetype(FONT_BOLD, int(size * SS))


def background():
    img = Image.new("RGB", (W * SS, H * SS))
    d = ImageDraw.Draw(img)
    for y in range(H * SS):
        t = y / (H * SS - 1)
        d.line([(0, y), (W * SS, y)], fill=tuple(int(lerp(a, b, t)) for a, b in zip(BG_TOP, BG_BOT)))
    return img


BG = background()


def draw_letter_backdrop(img, letter, strength, pulse):
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    d.text((W * SS // 2, int(H * SS * 0.46)), letter, font=font(340 + 14 * pulse),
           fill=(255, 255, 255, int(60 * strength)), anchor="mm")
    img.paste(over, (0, 0), over)


def dot(d, p, r, fill, outline=None, width=0):
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill, outline=outline, width=width)


def thick(d, pts, w, col):
    """Round-capped polyline with a dark outline."""
    for ww, c in ((w + 4 * SS * SCALE, EDGE), (w, col)):
        d.line(pts, fill=c, width=int(ww), joint="curve")
        for p in pts:
            dot(d, p, ww / 2, c)


def draw_hat(d, kind, hc, hr, k):
    """Hat drawn relative to head centre hc / radius hr (k = pixel unit)."""
    x, y = hc
    if kind == "hardhat":
        d.pieslice([x - hr * 1.1, y - hr * 1.25, x + hr * 1.1, y + hr * 0.95], 180, 360, fill=(255, 215, 30), outline=EDGE, width=int(1.5 * k))
        d.rectangle([x - hr * 1.3, y - hr * 0.3, x + hr * 1.3, y - hr * 0.05], fill=(255, 215, 30), outline=EDGE, width=int(1.5 * k))
        d.rectangle([x - hr * 0.12, y - hr * 1.15, x + hr * 0.12, y - hr * 0.3], fill=(230, 180, 20))
    elif kind == "cop":
        d.pieslice([x - hr * 1.05, y - hr * 1.3, x + hr * 1.05, y + hr * 0.7], 180, 360, fill=(24, 36, 90), outline=EDGE, width=int(1.5 * k))
        d.rectangle([x - hr * 1.1, y - hr * 0.35, x + hr * 1.1, y - hr * 0.08], fill=(10, 14, 40), outline=EDGE, width=int(1.5 * k))
        dot(d, (x, y - hr * 0.7), hr * 0.17, (255, 215, 30), EDGE, int(k))
    elif kind == "cowboy":
        d.ellipse([x - hr * 1.7, y - hr * 0.55, x + hr * 1.7, y + hr * 0.05], fill=(150, 100, 55), outline=EDGE, width=int(1.5 * k))
        d.pieslice([x - hr * 0.95, y - hr * 1.4, x + hr * 0.95, y + hr * 0.3], 180, 360, fill=(150, 100, 55), outline=EDGE, width=int(1.5 * k))
        d.rectangle([x - hr * 0.95, y - hr * 0.5, x + hr * 0.95, y - hr * 0.3], fill=(90, 55, 30))
    elif kind == "biker":
        d.pieslice([x - hr * 1.05, y - hr * 1.2, x + hr * 1.05, y + hr * 0.7], 180, 360, fill=(20, 20, 22), outline=EDGE, width=int(1.5 * k))
        d.polygon([(x - hr * 1.1, y - hr * 0.3), (x + hr * 1.1, y - hr * 0.3), (x + hr * 1.1, y - hr * 0.05), (x, y + hr * 0.1), (x - hr * 1.1, y - hr * 0.05)], fill=(20, 20, 22), outline=EDGE)
        dot(d, (x, y - hr * 0.7), hr * 0.14, (200, 200, 210))
    elif kind == "sailor":
        d.pieslice([x - hr * 1.0, y - hr * 1.3, x + hr * 1.0, y + hr * 0.7], 180, 360, fill=(250, 250, 252), outline=EDGE, width=int(1.5 * k))
        d.rectangle([x - hr * 1.05, y - hr * 0.35, x + hr * 1.05, y - hr * 0.05], fill=(30, 50, 120), outline=EDGE, width=int(1.5 * k))


def draw_figure(d, actor, pose, bounce, tilt, cx):
    k = SS * SCALE
    lean = pose["lean"] + tilt
    hip = (cx * SS, (392 + bounce) * SS - 116 * k)
    torso_len, arm_seg, leg_seg = 78 * k, 52 * k, 58 * k
    neck = seg(hip, 90 + lean, torso_len)
    ra_u, ra_f, la_u, la_f = pose["arms"]
    rl_u, rl_f, ll_u, ll_f = pose["legs"]

    # legs + shoes
    for a1, a2 in ((rl_u, rl_f), (ll_u, ll_f)):
        mid = seg(hip, a1, leg_seg)
        foot = seg(mid, a2, leg_seg)
        thick(d, [hip, mid, foot], 15 * k, actor["pants"])
        dot(d, foot, 9 * k, actor["shoes"], EDGE, int(1.5 * k))
    # torso
    thick(d, [hip, neck], 27 * k, actor["shirt"])
    if "vest" in actor:
        thick(d, [seg(hip, 90 + lean, 6 * k), seg(hip, 90 + lean, torso_len - 6 * k)], 19 * k, actor["vest"])
    if "collar" in actor:
        thick(d, [seg(neck, 90 + lean, -8 * k), neck], 22 * k, actor["collar"])
    if "bandana" in actor:
        thick(d, [seg(neck, 90 + lean, -4 * k), seg(neck, 90 + lean, 2 * k)], 15 * k, actor["bandana"])
    # belt
    dot(d, seg(hip, 90 + lean, 5 * k), 4 * k, (230, 200, 60))
    # arms
    sh_r = seg(neck, lean, 11 * k)
    sh_l = seg(neck, 180 + lean, 11 * k)
    sh_r, sh_l = (sh_r[0], sh_r[1] + 7 * k), (sh_l[0], sh_l[1] + 7 * k)
    for sh, a1, a2 in ((sh_r, ra_u, ra_f), (sh_l, la_u, la_f)):
        el = seg(sh, a1, arm_seg)
        hand = seg(el, a2, arm_seg)
        thick(d, [sh, el], 13 * k, actor["shirt"] if not actor["sleeve_skin"] else actor["shirt"])
        thick(d, [el, hand], 11 * k, actor["skin"] if actor["sleeve_skin"] or actor["role"] in ("sailor", "cop") else actor["shirt"])
        dot(d, hand, 7.5 * k, actor["skin"] if actor["role"] != "biker" else (20, 20, 22), EDGE, int(1.5 * k))
    # head
    hr = 20 * k
    hc = seg(neck, 90 + lean, 22 * k)
    dot(d, hc, hr, actor["skin"], EDGE, int(2 * k))
    draw_face(d, actor, hc, hr, k)
    draw_hat(d, actor["hat"], hc, hr, k)


def draw_face(d, actor, hc, hr, k):
    x, y = hc
    if actor.get("shades"):
        d.rectangle([x - hr * 0.85, y - hr * 0.3, x - hr * 0.1, y + hr * 0.1], fill=(15, 15, 20))
        d.rectangle([x + hr * 0.1, y - hr * 0.3, x + hr * 0.85, y + hr * 0.1], fill=(15, 15, 20))
        d.line([(x - hr * 0.1, y - hr * 0.22), (x + hr * 0.1, y - hr * 0.22)], fill=(15, 15, 20), width=int(1.5 * k))
    else:
        for sx in (-1, 1):
            dot(d, (x + sx * hr * 0.38, y - hr * 0.12), 2.2 * k, EDGE)
    if actor.get("stache"):
        d.pieslice([x - hr * 0.6, y + hr * 0.05, x + hr * 0.6, y + hr * 0.6], 180, 360, fill=(40, 24, 16))
        d.arc([x - hr * 0.35, y + hr * 0.3, x + hr * 0.35, y + hr * 0.8], 20, 160, fill=EDGE, width=int(1.5 * k))
    else:
        d.arc([x - hr * 0.5, y - hr * 0.1, x + hr * 0.5, y + hr * 0.65], 20, 160, fill=EDGE, width=int(2 * k))


def draw_floor(d):
    y = 392 * SS
    d.rectangle([0, y, W * SS, H * SS], fill=(30, 10, 60))
    d.line([(0, y), (W * SS, y)], fill=(255, 120, 200), width=3 * SS)


def draw_header(d, current):
    f = font(44)
    gap = 84
    x0 = W // 2 - int(1.5 * gap)
    for i, ch in enumerate(ORDER):
        on = ch == current
        d.text(((x0 + i * gap) * SS, 40 * SS), ch, font=f, anchor="mm",
               fill=(255, 255, 255) if on else (150, 110, 190),
               stroke_width=(3 if on else 0) * SS, stroke_fill=(255, 90, 160))


def draw_caption(d, current):
    f = font(26)
    pieces = [("It's fun to work on the ", None)]
    for i, ch in enumerate(ORDER):
        pieces.append((ch, ch))
        if i < len(ORDER) - 1:
            pieces.append((" ", None))
    total = sum(d.textlength(t, font=f) for t, _ in pieces)
    x = (W * SS - total) / 2
    y = 436 * SS
    for t, ch in pieces:
        hot = ch is not None and ch == current
        d.text((x, y), t, font=f, anchor="lm",
               fill=(255, 226, 64) if hot else (255, 255, 255),
               stroke_width=(2 if hot else 0) * SS, stroke_fill=(255, 90, 160))
        x += d.textlength(t, font=f)


def render(pose, current, bounce, tilt, pulse, strength):
    img = BG.copy().convert("RGBA")
    draw_letter_backdrop(img, current, strength, pulse)
    d = ImageDraw.Draw(img)
    draw_floor(d)
    draw_header(d, current)
    x0 = W / 2 - SPACING * (len(CAST) - 1) / 2
    for i, actor in enumerate(CAST):
        draw_figure(d, actor, pose, bounce, tilt, x0 + i * SPACING)
    draw_caption(d, current)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def main():
    frames = []
    n_trans, n_hold = 4, 8
    for i, ch in enumerate(ORDER):
        prev, cur = POSES[ORDER[i - 1]], POSES[ch]
        for k in range(n_trans):
            t = (k + 1) / (n_trans + 1)
            frames.append(render(pose_mix(prev, cur, t), ch if t > 0.5 else ORDER[i - 1],
                                 bounce=-10 * math.sin(math.pi * t), tilt=0, pulse=0, strength=0.6))
        for k in range(n_hold):
            ph = k / n_hold * 2 * math.pi
            frames.append(render(cur, ch, bounce=4 * math.sin(2 * ph), tilt=3 * math.sin(ph),
                                 pulse=math.sin(2 * ph), strength=1.0))
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=85, loop=0, disposal=2)
    if PREVIEW_DIR:
        for i, ch in enumerate(ORDER):
            frames[i * (n_trans + n_hold) + n_trans + 2].save(os.path.join(PREVIEW_DIR, f"adlc_{ch}.png"))
    print(len(frames), "frames")


if __name__ == "__main__":
    main()
