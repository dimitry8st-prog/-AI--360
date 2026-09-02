"""Brand frames for the 60s promo. Demo names only — no secrets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INDIGO = (79, 70, 229)
NAVY = (30, 58, 138)
ORANGE = (249, 115, 22)
BG = (248, 250, 252)
WHITE = (255, 255, 255)
TEXT = (17, 24, 39)
MUTED = (100, 116, 139)
LINE = (226, 232, 240)
OK = (16, 185, 129)
GITHUB = "github.com/dimitry8st-prog/-AI--360"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = Path(r"C:\Windows\Fonts") / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def _round_rect(draw: ImageDraw.ImageDraw, box, fill, radius=18, outline=None):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


FOX_PATH = Path(__file__).resolve().parents[1] / "assets" / "dis-fox.jpg"


def _fox() -> Image.Image:
    return Image.open(FOX_PATH).convert("RGB")


def paste_fox(
    base: Image.Image,
    box: tuple[int, int, int, int],
    *,
    cover: bool = False,
    radius: int = 24,
    fill: tuple[int, int, int] = BG,
) -> None:
    """Fit the full fox in `box` (contain) unless cover=True for tiny avatars."""
    x0, y0, x1, y1 = [int(v) for v in box]
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    src = _fox()
    sw, sh = src.size
    if cover:
        scale = max(bw / sw, bh / sh)
    else:
        scale = min(bw / sw, bh / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (bw, bh), fill)
    if cover:
        left = max(0, (nw - bw) // 2)
        top = max(0, (nh - bh) // 2)
        canvas = src.crop((left, top, left + bw, top + bh))
    else:
        canvas.paste(src, ((bw - nw) // 2, (bh - nh) // 2))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=max(0, radius), fill=255)
    base.paste(canvas, (x0, y0), mask)


@dataclass
class Canvas:
    w: int
    h: int
    vertical: bool

    @property
    def pad(self) -> int:
        return 56 if self.vertical else 72

    def blank(self) -> Image.Image:
        img = Image.new("RGB", (self.w, self.h), BG)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, self.w, 8), fill=INDIGO)
        d.rectangle((0, self.h - 8, self.w, self.h), fill=ORANGE)
        return img

    def title_block(self, img: Image.Image, kicker: str, title: str, y: int | None = None) -> int:
        d = ImageDraw.Draw(img)
        y = self.pad + (80 if self.vertical else 36) if y is None else y
        kf = _font(22 if self.vertical else 20, True)
        tf = _font(44 if self.vertical else 42, True)
        d.text((self.pad, y), kicker.upper(), fill=ORANGE, font=kf)
        y += 40
        for line in _wrap(d, title, tf, self.w - self.pad * 2):
            d.text((self.pad, y), line, fill=TEXT, font=tf)
            y += 54 if self.vertical else 52
        return y + 16


def scene_problem(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Проблема", "Обучение сотрудников снова превращается в ручную работу?")
    d = ImageDraw.Draw(img)
    cards = [
        ("Таблицы учёта", "12 файлов · без единого статуса"),
        ("Чаты и письма", "Одинаковые вопросы каждый день"),
        ("Курс не завершён", "Командная работа · 0%"),
    ]
    gap = 18
    if c.vertical:
        cw, ch = c.w - c.pad * 2, 150
        for i, (h, s) in enumerate(cards):
            x, yy = c.pad, y + i * (ch + gap)
            _round_rect(d, (x, yy, x + cw, yy + ch), WHITE, outline=LINE)
            d.text((x + 24, yy + 28), h, fill=TEXT, font=_font(26, True))
            d.text((x + 24, yy + 78), s, fill=MUTED, font=_font(20))
    else:
        cw = (c.w - c.pad * 2 - gap * 2) // 3
        ch = 220
        for i, (h, s) in enumerate(cards):
            x = c.pad + i * (cw + gap)
            _round_rect(d, (x, y, x + cw, y + ch), WHITE, outline=LINE)
            d.rectangle((x, y, x + 8, y + ch), fill=ORANGE)
            d.text((x + 28, y + 36), h, fill=TEXT, font=_font(24, True))
            for j, line in enumerate(_wrap(d, s, _font(18), cw - 48)):
                d.text((x + 28, y + 90 + j * 28), line, fill=MUTED, font=_font(18))
    return img


def scene_solution(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Решение", "Знакомьтесь: ДИС — AI-наставник 360")
    d = ImageDraw.Draw(img)
    panel = [
        "Единая система обучения",
        "Практика по утверждённым материалам",
        "Контроль знаний без кадровых решений ИИ",
    ]
    if c.vertical:
        side = min(c.w - c.pad * 2, 900)
        paste_fox(img, (c.pad, y, c.pad + side, y + side), radius=28, fill=BG)
        py = y + side + 24
        pw = c.w - c.pad * 2
        px = c.pad
    else:
        side = min(520, c.h - y - 48)
        paste_fox(img, (c.pad, y, c.pad + side, y + side), radius=28, fill=BG)
        px = c.pad + side + 28
        py = y
        pw = c.w - c.pad - px
    _round_rect(d, (px, py, px + pw, py + (220 if c.vertical else 240)), WHITE, outline=LINE)
    for i, line in enumerate(panel):
        d.ellipse((px + 24, py + 28 + i * 62, px + 40, py + 44 + i * 62), fill=INDIGO)
        d.text((px + 56, py + 22 + i * 62), line, fill=TEXT, font=_font(22, True))
    return img


def scene_telegram(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Telegram", "Обучение доступно прямо в Telegram")
    d = ImageDraw.Draw(img)
    tags = ["Курсы", "Ответы на вопросы", "Продолжение обучения", "Персональный прогресс"]
    tx = c.pad
    for tag in tags:
        tw = int(d.textlength(tag, font=_font(18, True))) + 28
        _round_rect(d, (tx, y, tx + tw, y + 40), (238, 242, 255), radius=20)
        d.text((tx + 14, y + 8), tag, fill=INDIGO, font=_font(18, True))
        tx += tw + 10
        if tx > c.w - c.pad - 80:
            tx = c.pad
            y += 50
    y += 70
    phone_w = min(420, c.w - c.pad * 2)
    phone_h = 520 if c.vertical else 420
    px = (c.w - phone_w) // 2
    _round_rect(d, (px, y, px + phone_w, y + phone_h), WHITE, radius=36, outline=LINE)
    d.rectangle((px, y, px + phone_w, y + 64), fill=INDIGO)
    paste_fox(img, (px + 16, y + 10, px + 56, y + 50), cover=True, radius=20)
    d.text((px + 68, y + 18), "ДИС · курс", fill=WHITE, font=_font(22, True))
    bubbles = [
        (False, "Командная работа и коммуникация"),
        (True, "Что такое активное слушание?"),
        (False, "По утверждённому модулю: сначала уточните факт, затем перескажите смысл."),
    ]
    by = y + 88
    for mine, text in bubbles:
        font = _font(18)
        lines = _wrap(d, text, font, phone_w - 80)
        bh = 24 + 26 * len(lines)
        bw = phone_w - 56
        bx = px + 28 if not mine else px + phone_w - 28 - bw
        fill = (238, 242, 255) if not mine else (255, 247, 237)
        _round_rect(d, (bx, by, bx + bw, by + bh), fill, radius=14)
        for i, line in enumerate(lines):
            d.text((bx + 14, by + 10 + i * 26), line, fill=TEXT, font=font)
        by += bh + 14
    d.text((px + 28, y + phone_h - 48), "Прогресс 38%", fill=MUTED, font=_font(18, True))
    d.rounded_rectangle((px + 28, y + phone_h - 24, px + phone_w - 28, y + phone_h - 14), 6, fill=(238, 242, 255))
    d.rounded_rectangle((px + 28, y + phone_h - 24, px + 28 + int((phone_w - 56) * 0.38), y + phone_h - 14), 6, fill=ORANGE)
    return img


def scene_roles(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Разделение ролей", "Наставник, практика и экзамен — разные компоненты")
    d = ImageDraw.Draw(img)
    cols = [
        ("AI-наставник", "Объясняет материал и цитирует источники"),
        ("Конструктор", "Готовит практику. Вопросы в экзамен сам не кладёт"),
        ("Экзаменатор", "Проверяет по утверждённой рубрике"),
    ]
    gap = 16
    if c.vertical:
        ch = 170
        cw = c.w - c.pad * 2
        for i, (h, s) in enumerate(cols):
            yy = y + i * (ch + gap)
            _round_rect(d, (c.pad, yy, c.pad + cw, yy + ch), WHITE, outline=LINE)
            d.rectangle((c.pad, yy, c.pad + 10, yy + ch), fill=INDIGO if i < 2 else ORANGE)
            d.text((c.pad + 28, yy + 28), f"{i + 1}. {h}", fill=TEXT, font=_font(26, True))
            for j, line in enumerate(_wrap(d, s, _font(20), cw - 56)):
                d.text((c.pad + 28, yy + 78 + j * 28), line, fill=MUTED, font=_font(20))
    else:
        cw = (c.w - c.pad * 2 - gap * 2) // 3
        ch = 260
        for i, (h, s) in enumerate(cols):
            x = c.pad + i * (cw + gap)
            _round_rect(d, (x, y, x + cw, y + ch), WHITE, outline=LINE)
            d.text((x + 24, y + 28), f"{i + 1}", fill=ORANGE, font=_font(36, True))
            d.text((x + 24, y + 88), h, fill=TEXT, font=_font(24, True))
            yy = y + 140
            for line in _wrap(d, s, _font(18), cw - 48):
                d.text((x + 24, yy), line, fill=MUTED, font=_font(18))
                yy += 28
    return img


def scene_panel(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Web-панель", "Всё главное — в единой панели")
    d = ImageDraw.Draw(img)
    tags = ["Назначения", "Прогресс", "Результаты", "Контроль"]
    tx = c.pad
    for tag in tags:
        tw = int(d.textlength(tag, font=_font(18, True))) + 28
        _round_rect(d, (tx, y, tx + tw, y + 38), INDIGO, radius=18)
        d.text((tx + 14, y + 8), tag, fill=WHITE, font=_font(18, True))
        tx += tw + 10
    y += 70
    rows = [
        ("Командная работа и коммуникация", "38%", "in_progress"),
        ("Онбординг руководителя", "100%", "completed"),
        ("Коммуникация с заказчиком", "0%", "assigned"),
    ]
    _round_rect(d, (c.pad, y, c.w - c.pad, y + (320 if c.vertical else 280)), WHITE, outline=LINE)
    d.text((c.pad + 24, y + 18), "Иван Сотрудников · демо", fill=MUTED, font=_font(18))
    ry = y + 56
    for title, pct, status in rows:
        d.text((c.pad + 24, ry), title, fill=TEXT, font=_font(22, True))
        bar_x = c.pad + 24
        bar_w = c.w - c.pad * 2 - 200
        d.rounded_rectangle((bar_x, ry + 40, bar_x + bar_w, ry + 50), 6, fill=(238, 242, 255))
        d.rounded_rectangle((bar_x, ry + 40, bar_x + int(bar_w * int(pct.strip("%")) / 100), ry + 50), 6, fill=OK if pct == "100%" else INDIGO)
        d.text((c.w - c.pad - 160, ry + 8), f"{pct} · {status}", fill=MUTED, font=_font(18, True))
        ry += 84
    return img


def scene_result(c: Canvas) -> Image.Image:
    img = c.blank()
    y = c.title_block(img, "Результат", "Разрозненное обучение → управляемая система")
    d = ImageDraw.Draw(img)
    points = [
        "Меньше ручной работы",
        "Единые стандарты обучения",
        "Прозрачный прогресс",
        "Контроль со стороны человека",
    ]
    for i, p in enumerate(points):
        yy = y + i * (88 if c.vertical else 78)
        _round_rect(d, (c.pad, yy, c.w - c.pad, yy + 70), WHITE, outline=LINE)
        d.ellipse((c.pad + 22, yy + 22, c.pad + 46, yy + 46), fill=ORANGE)
        d.text((c.pad + 64, yy + 18), p, fill=TEXT, font=_font(26 if c.vertical else 24, True))
    return img


def scene_finale(c: Canvas) -> Image.Image:
    img = Image.new("RGB", (c.w, c.h), NAVY)
    bar = 340 if c.vertical else 290
    paste_fox(img, (32, 24, c.w - 32, c.h - bar), cover=False, radius=20, fill=NAVY)
    d = ImageDraw.Draw(img)
    ty = c.h - bar + (20 if c.vertical else 16)
    tf = _font(44 if c.vertical else 48, True)
    sf = _font(24 if c.vertical else 26)
    title = "AI-наставник 360"
    tw = d.textlength(title, font=tf)
    d.text(((c.w - tw) / 2, ty), title, fill=WHITE, font=tf)
    sub = "Обучение. Практика. Контроль знаний."
    sw = d.textlength(sub, font=sf)
    d.text(((c.w - sw) / 2, ty + 58), sub, fill=ORANGE, font=sf)
    cta = "Подготовьте команду к реальным задачам"
    cf = _font(20)
    cw = d.textlength(cta, font=cf)
    d.text(((c.w - cw) / 2, ty + 100), cta, fill=(253, 186, 116), font=cf)
    author = "Автор проекта: Степанов Д.А."
    aw = d.textlength(author, font=_font(18, True))
    d.text(((c.w - aw) / 2, ty + 148), author, fill=WHITE, font=_font(18, True))
    gw = d.textlength(GITHUB, font=_font(16))
    d.text(((c.w - gw) / 2, ty + 180), GITHUB, fill=(199, 210, 254), font=_font(16))
    return img


SCENES = [
    ("01-problem", 7.0, scene_problem),
    ("02-solution", 8.0, scene_solution),
    ("03-telegram", 10.0, scene_telegram),
    ("04-roles", 10.0, scene_roles),
    ("05-panel", 12.0, scene_panel),
    ("06-result", 8.0, scene_result),
    ("07-finale", 5.0, scene_finale),
]


def render_all(out_dir: Path, width: int, height: int) -> list[tuple[Path, float]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(width, height, vertical=height > width)
    files = []
    for name, dur, fn in SCENES:
        path = out_dir / f"{name}.png"
        fn(canvas).save(path, "PNG")
        files.append((path, dur))
    return files
