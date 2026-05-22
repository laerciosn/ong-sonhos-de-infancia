"""
Gerador do logo PNG 500×500 da ONG Sonhos de Infância.
Trabalha a 4× (2000×2000) para anti-aliasing por supersampling, depois reduz.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

SCALE = 4
SZ    = 500 * SCALE   # 2000 × 2000

img = Image.new('RGBA', (SZ, SZ), (0, 0, 0, 0))

def rgb(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)

PINK_FILL  = rgb('f387ab')
PINK_DARK  = rgb('c94080')
PINK_HAND  = rgb('f06898')   # rosa mais escuro/saturado p/ distinguir do coração
ORANGE     = rgb('f28741')
BLUE       = rgb('6ac3c9')
GREEN      = rgb('9ccc32')
YELLOW     = rgb('f4b72b')
RED        = rgb('ed4832')
PURPLE     = rgb('9b59b6')
DARK       = rgb('333333')
WHITE      = (255, 255, 255, 255)

# ── Posição e tamanho do coração ──────────────────────────
CX = SZ // 2
CY = int(SZ * 0.557)   # ≈ y=278 em coords 1×
HS = 9.5 * SCALE       # escala do coração

def heart_pts(cx, cy, scale, n=800):
    """Fórmula paramétrica clássica do coração."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x =  16 * math.sin(t)**3
        y = (13*math.cos(t) - 5*math.cos(2*t)
              - 2*math.cos(3*t)   - math.cos(4*t))
        pts.append((cx + x*scale, cy - y*scale))
    return pts

draw = ImageDraw.Draw(img)

# Sombra suave
sh = Image.new('RGBA', (SZ, SZ), (0,0,0,0))
ImageDraw.Draw(sh).polygon(
    heart_pts(CX + SCALE*4, CY + SCALE*10, HS), fill=(0,0,0,55))
sh = sh.filter(ImageFilter.GaussianBlur(SCALE * 14))
img = Image.alpha_composite(img, sh)
draw = ImageDraw.Draw(img)

# Borda do coração (simula stroke desenhando maior com cor escura)
draw.polygon(heart_pts(CX, CY, HS + SCALE*5.5), fill=PINK_DARK)
# Preenchimento
draw.polygon(heart_pts(CX, CY, HS),             fill=PINK_FILL)

# Brilho (gloss) no canto superior-esquerdo
gl = Image.new('RGBA', (SZ, SZ), (0,0,0,0))
gd = ImageDraw.Draw(gl)
gw, gh = int(SCALE*100), int(SCALE*58)
gcx = CX - int(SCALE*45)
gcy = CY - int(SCALE*75)
gd.ellipse([gcx-gw//2, gcy-gh//2, gcx+gw//2, gcy+gh//2],
            fill=(255,255,255,48))
img = Image.alpha_composite(img, gl.rotate(32, resample=Image.BICUBIC))
draw = ImageDraw.Draw(img)


# ── Função para desenhar uma mãozinha ────────────────────
def draw_hand(base, cx_1x, cy_1x, color, angle_deg, sz_1x=37):
    """
    Desenha palma + 4 dedos + polegar com stroke branco,
    rotaciona e cola em base na posição (cx_1x, cy_1x) em coords 1×.
    """
    s  = sz_1x * SCALE
    sw = max(1, int(s * 0.13))   # largura do stroke branco

    cw = ch = int(s * 7)         # canvas grande p/ rotação sem corte
    ocx = cw // 2
    ocy = ch // 2 + int(s * 0.35)

    stk = Image.new('RGBA', (cw, ch), (0,0,0,0))
    col = Image.new('RGBA', (cw, ch), (0,0,0,0))
    sd  = ImageDraw.Draw(stk)
    hd  = ImageDraw.Draw(col)

    # Palma
    pw = int(s * 2.44);  ph = int(s * 1.40);  pr = int(s * 0.56)

    # Dedos: [mindinho, anelar, médio, indicador]
    fxo = [-int(s*.87), -int(s*.29), int(s*.29), int(s*.87)]
    fw  = int(s * 0.52)
    fhs = [int(s*1.68), int(s*1.96), int(s*2.02), int(s*1.72)]
    fb  = ocy - ph//2 + int(s*0.22)   # base do dedo (toca a palma)

    # Polegar
    tw = int(s*0.50);  th = int(s*1.10)
    tx = ocx - pw//2 - tw//2 - sw + int(s*0.04)
    ty = ocy - int(s*0.16)

    # — Stroke branco (camada inferior) —
    for i, fx in enumerate(fxo):
        x  = ocx + fx
        ft = fb - fhs[i]
        sd.rounded_rectangle([x-fw//2-sw, ft-sw, x+fw//2+sw, fb+sw],
                               radius=fw//2+sw, fill=WHITE)
    sd.rounded_rectangle([ocx-pw//2-sw, ocy-ph//2-sw,
                           ocx+pw//2+sw, ocy+ph//2+sw],
                          radius=pr+sw, fill=WHITE)
    sd.ellipse([tx-tw//2-sw*2, ty-th//2-sw,
                tx+tw//2+sw*2, ty+th//2+int(s*.12)+sw], fill=WHITE)

    # — Cor (camada superior) —
    for i, fx in enumerate(fxo):
        x  = ocx + fx
        ft = fb - fhs[i]
        hd.rounded_rectangle([x-fw//2, ft, x+fw//2, fb],
                               radius=fw//2, fill=color)
    hd.rounded_rectangle([ocx-pw//2, ocy-ph//2,
                           ocx+pw//2, ocy+ph//2],
                          radius=pr, fill=color)
    hd.ellipse([tx-tw//2, ty-th//2,
                tx+tw//2, ty+th//2+int(s*.12)], fill=color)

    # Compõe stroke + cor, rotaciona, cola
    hand = Image.alpha_composite(stk, col)
    rotated = hand.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)

    rx = int(cx_1x * SCALE) - rotated.width  // 2
    ry = int(cy_1x * SCALE) - rotated.height // 2
    base.paste(rotated, (rx, ry), rotated)


# ── Posições das mãozinhas (coords 1× / 500px) ───────────
#   Fileira 1 (lóbulos sup):  laranja (esq) · azul (dir)
#   Fileira 2 (meio):         vermelho · roxo · verde
#   Fileira 3 (inferior):     amarelo · rosa
hands = [
    (175, 200, ORANGE,  -10),
    (325, 200, BLUE,     10),
    (148, 278, RED,     -22),
    (250, 278, PURPLE,    0),
    (352, 278, GREEN,    22),
    (192, 335, YELLOW,  -10),
    (308, 335, PINK_HAND, 10),
]

for hx, hy, color, angle in hands:
    draw_hand(img, hx, hy, color, angle)

draw = ImageDraw.Draw(img)


# ── Texto em arco ─────────────────────────────────────────
TEXT = "SONHOS DE INFÂNCIA"
FS   = 22 * SCALE   # tamanho da fonte no canvas 4×

font = None
for fp in [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
]:
    try:
        font = ImageFont.truetype(fp, FS)
        print(f"Fonte: {fp}")
        break
    except:
        pass
if font is None:
    print("Usando fonte padrão")
    font = ImageFont.load_default()

# Parâmetros do arco (coords 1×)
ARC_CX = 250
ARC_CY = 278.0
ARC_R  = 183

arc_cx = int(ARC_CX * SCALE)
arc_cy = int(ARC_CY * SCALE)
arc_r  = int(ARC_R  * SCALE)

# Mede largura de cada caractere
tmp_img  = Image.new('RGBA', (1, 1))
tmp_draw = ImageDraw.Draw(tmp_img)
LS = int(FS * 0.12)   # espaçamento entre letras

widths = []
for ch in TEXT:
    bb = tmp_draw.textbbox((0, 0), ch, font=font)
    widths.append(bb[2] - bb[0])

total_px  = sum(widths) + LS * (len(TEXT) - 1)
total_deg = math.degrees(total_px / arc_r)
start_deg = 270 - total_deg / 2   # 270° = topo do círculo

x_cur = 0
for i, ch in enumerate(TEXT):
    cw      = widths[i]
    mid_px  = x_cur + cw / 2
    ch_deg  = start_deg + math.degrees(mid_px / arc_r)
    ch_rad  = math.radians(ch_deg)

    ch_x = arc_cx + arc_r * math.cos(ch_rad)
    ch_y = arc_cy + arc_r * math.sin(ch_rad)
    rot  = ch_deg - 270   # 0° = vertical, cresce no sentido horário

    bw = cw + FS * 2
    bh = FS * 2
    ch_img = Image.new('RGBA', (int(bw), int(bh)), (0, 0, 0, 0))
    cd     = ImageDraw.Draw(ch_img)

    hw = int(FS * 0.15)
    tx = int(bw // 2 - cw // 2)
    ty = int(bh // 2 - FS // 2)

    # Halo branco (8 direções)
    for ddx, ddy in [(-hw,0),(hw,0),(0,-hw),(0,hw),
                      (-hw,-hw),(hw,-hw),(-hw,hw),(hw,hw)]:
        cd.text((tx+ddx, ty+ddy), ch, font=font, fill=WHITE)
    # Texto escuro
    cd.text((tx, ty), ch, font=font, fill=DARK)

    rotated_ch = ch_img.rotate(-rot, resample=Image.BICUBIC, expand=False)
    rx = int(ch_x) - rotated_ch.width  // 2
    ry = int(ch_y) - rotated_ch.height // 2
    img.paste(rotated_ch, (rx, ry), rotated_ch)

    x_cur += cw + LS


# ── Redimensiona para 500×500 e salva ────────────────────
final    = img.resize((500, 500), Image.LANCZOS)
out_path = r"D:\claude code\ong-sonhos-de-infancia\logo.png"
final.save(out_path, 'PNG')
print(f"\n✓ Salvo: {out_path}")
print(f"  Tamanho: {final.size[0]}×{final.size[1]} px")
