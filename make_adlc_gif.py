"""Render a YMCA-style dance GIF where the dancer spells A, D, L, C."""
import math
from PIL import Image, ImageDraw, ImageFont

W = H = 480
SS = 2  # supersampling factor
OUT = "adlc-dance.gif"

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
FIG = (255, 226, 64)
FIG_EDGE = (60, 20, 70)
GLOW = (255, 255, 255)


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
    return ImageFont.truetype(FONT_BOLD, size * SS)


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
    f = font(int(300 + 14 * pulse))
    d.text((W * SS // 2, int(H * SS * 0.44)), letter, font=f, fill=(255, 255, 255, int(70 * strength)), anchor="mm")
    img.paste(over, (0, 0), over)


def draw_figure(d, pose, bounce, tilt):
    cx, hip_y = 240 * SS, (292 + bounce) * SS
    s = SS
    lean = pose["lean"] + tilt
    torso_len, arm_seg, leg_seg = 78 * s, 52 * s, 58 * s

    hip = (cx, hip_y)
    neck = seg(hip, 90 + lean, torso_len)
    lw = 11 * s

    def limb(start, a1, a2, l1, l2, col=FIG):
        mid = seg(start, a1, l1)
        end = seg(mid, a2, l2)
        for w, c in ((lw + 5 * s, FIG_EDGE), (lw, col)):
            d.line([start, mid, end], fill=c, width=w, joint="curve")
            for p in (start, mid, end):
                d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=c)
        return end

    ra_u, ra_f, la_u, la_f = pose["arms"]
    rl_u, rl_f, ll_u, ll_f = pose["legs"]

    # legs
    feet = []
    for a1, a2 in ((rl_u, rl_f), (ll_u, ll_f)):
        feet.append(limb(hip, a1, a2, leg_seg, leg_seg))
    # torso
    for w, c in ((lw + 5 * s, FIG_EDGE), (lw + 2 * s, FIG)):
        d.line([hip, neck], fill=c, width=w)
        for p in (hip, neck):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=c)
    # shoes
    for (fx, fy), a in zip(feet, (rl_f, ll_f)):
        r = 9 * s
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(255, 90, 90), outline=FIG_EDGE, width=2 * s)
    # arms (from shoulders)
    sh_r = seg(neck, lean, 13 * s)
    sh_l = seg(neck, 180 + lean, 13 * s)
    sh_r = (sh_r[0], sh_r[1] + 6 * s)
    sh_l = (sh_l[0], sh_l[1] + 6 * s)
    hands = [limb(sh_r, ra_u, ra_f, arm_seg, arm_seg), limb(sh_l, la_u, la_f, arm_seg, arm_seg)]
    for hx, hy in hands:
        r = 8 * s
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=FIG, outline=FIG_EDGE, width=2 * s)
    # head
    head_c = seg(neck, 90 + lean, 24 * s)
    hr = 24 * s
    d.ellipse([head_c[0] - hr, head_c[1] - hr, head_c[0] + hr, head_c[1] + hr], fill=FIG, outline=FIG_EDGE, width=3 * s)
    ex = 8 * s
    for sx in (-1, 1):
        ex_c = (head_c[0] + sx * ex, head_c[1] - 4 * s)
        d.ellipse([ex_c[0] - 3 * s, ex_c[1] - 4 * s, ex_c[0] + 3 * s, ex_c[1] + 4 * s], fill=FIG_EDGE)
    d.arc([head_c[0] - 12 * s, head_c[1] - 8 * s, head_c[0] + 12 * s, head_c[1] + 12 * s], 20, 160, fill=FIG_EDGE, width=3 * s)


def draw_floor(d):
    y = 372 * SS
    d.rectangle([0, y, W * SS, H * SS], fill=(30, 10, 60))
    d.line([(0, y), (W * SS, y)], fill=(255, 120, 200), width=3 * SS)


def draw_header(d, current):
    f = font(46)
    gap = 84 * SS
    x0 = W * SS // 2 - int(1.5 * gap)
    for i, ch in enumerate(ORDER):
        on = ch == current
        d.text((x0 + i * gap, 44 * SS), ch, font=f, anchor="mm",
               fill=(255, 255, 255) if on else (255, 255, 255, 0) if False else (150, 110, 190),
               stroke_width=(3 if on else 0) * SS, stroke_fill=(255, 90, 160))


def draw_caption(d, current):
    f = font(22)
    parts = [("It's fun to work on the ", None)] + [(ch, ch) for ch in ORDER]
    pieces = []
    for text, ch in parts:
        pieces.append((text, ch))
        if ch is not None and ch != ORDER[-1]:
            pieces.append((" ", None))
    total = sum(d.textlength(t, font=f) for t, _ in pieces)
    x = (W * SS - total) / 2
    y = 424 * SS
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
    draw_figure(d, pose, bounce, tilt)
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
    for i, ch in enumerate(ORDER):  # contact sheet frames for review
        frames[i * (n_trans + n_hold) + n_trans + 2].save(f"/tmp/claude-0/-home-user-claude-playground/352e9488-741c-5873-9c7a-7dbead46f232/scratchpad/adlc_{ch}.png")
    print(len(frames), "frames")


if __name__ == "__main__":
    main()
