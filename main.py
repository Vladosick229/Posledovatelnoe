import sys
import tkinter as tk
from tkinter import ttk
import time
import os
import ctypes
from PIL import Image, ImageTk
import cv2
import numpy as np

# PyInstaller resource path helper
def resource_path(rel):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.dirname(__file__)
    return os.path.join(base, rel)

class AudioPlayer:
    """Plays the pre-recorded narration tracks through the Windows MCI API.

    MCI is used instead of winsound because it supports pause/resume and
    starting playback from an arbitrary position (needed for timing).
    """

    _ALIAS = "narration_track"

    def __init__(self):
        self._mci = ctypes.windll.winmm.mciSendStringW
        self._buffer = ctypes.create_unicode_buffer(512)
        self._open_path = None

    def _cmd(self, command):
        error = self._mci(command, self._buffer, len(self._buffer), None)
        return error, self._buffer.value

    def play(self, path, start_ms=0):
        self.stop()
        if not path or not os.path.exists(path):
            return False
        error, _ = self._cmd('open "%s" type waveaudio alias %s' % (path, self._ALIAS))
        if error:
            return False
        self._cmd("set %s time format milliseconds" % self._ALIAS)
        error, _ = self._cmd("play %s from %d" % (self._ALIAS, max(0, int(start_ms))))
        if error:
            self._cmd("close %s" % self._ALIAS)
            return False
        self._open_path = path
        return True

    def pause(self):
        if self._open_path:
            self._cmd("pause %s" % self._ALIAS)

    def resume(self):
        if self._open_path:
            self._cmd("resume %s" % self._ALIAS)

    def stop(self):
        if self._open_path:
            self._cmd("stop %s" % self._ALIAS)
            self._cmd("close %s" % self._ALIAS)
            self._open_path = None

# Text shown in the speech bubble at the start of each phase. It follows the
# recorded narration, but is shortened where the bubble would overflow.
PHASE_SPEECH = [
    "Свойство последовательного соединения можно продемонстрировать с помощью несложного опыта. Нам понадобятся два резистора: R1 = 100 Ом и R2 с переменным сопротивлением.",
    "Для определения силы тока и напряжений будем использовать миллиамперметр и три вольтметра.",
    "Для получения экспериментальных данных будем использовать источник постоянного напряжения 12 В.",
    "Собираем электрическую цепь. Амперметр включается последовательно, а вольтметры — параллельно.",
    "R2 = 200 Ом. Амперметр показывает 40 мА, вольтметры — 4 В, 8 В и 12 В.",
    "С помощью этих показаний подтверждаются два основных свойства последовательного соединения.",
    "По показаниям приборов, используя закон Ома, можно рассчитать сопротивление цепи: Rэкв = 100 + 200 = 300 Ом.",
    "При уменьшении сопротивления сила тока в цепи увеличивается, напряжения на участках изменяются, а их сумма равна общему напряжению.",
]

C_BG          = "#f5f0e8"
C_RESISTOR    = "#D32F2F"
C_RESISTOR_BG = "#FFCDD2"
C_WIRE_SERIES = "#1565C0"
C_WIRE_BRANCH = "#2E7D32"
C_METER_BG    = "#E0E0E0"
C_METER_BORDER= "#424242"
C_BATTERY     = "#E65100"
C_TEXT        = "#212121"
C_PANEL_BG    = "#FFFFFF"
C_PANEL_BORDER= "#BDBDBD"
C_R2_ARROW    = "#E65100"
C_TABLE_HEADER= "#37474F"
C_SPEECH_BG   = "#FFFFFF"
C_SPEECH_BORDER = "#FFB300"

DX, DY = 60, -200
N_TOP_LEFT   = (325+DX, 363+DY)
N_BEFORE_R1  = (600+DX, 363+DY)
N_AFTER_R1   = (900+DX, 363+DY)
N_TOP_RIGHT  = (1200+DX, 363+DY)
N_BOT_RIGHT  = (1200+DX, 790+DY)
N_BOT_LEFT   = (325+DX, 790+DY)

PA1_CENTER   = (463+DX, 363+DY)
R1_LEFT      = 656+DX; R1_RIGHT = 850+DX; R1_Y = 363+DY
R2_LEFT      = 956+DX; R2_RIGHT = 1150+DX; R2_Y = 363+DY
E1_X = 325+DX; E1_Y1 = 450+DY; E1_Y2 = 688+DY
PV1_CENTER   = (750+DX, 500+DY)
PV2_CENTER   = (1050+DX, 588+DY)
PV3_CENTER   = (900+DX, 713+DY)

METER_W        = 92
METER_H        = 76
METER_PIVOT_DY = 26
METER_RARC     = 40
METER_NEEDLE_LEN  = 36
METER_NEEDLE_TAIL = 7
METER_ANG0     = -150.0
METER_ANG1     = -30.0


def _meter_angle(kind, v):
    if kind == "A":
        vmin, vmax = 0.0, 120.0
    else:
        vmin, vmax = 0.0, 15.0
    if v < vmin:
        v = vmin
    elif v > vmax:
        v = vmax
    return METER_ANG0 + (v - vmin) / (vmax - vmin) * (METER_ANG1 - METER_ANG0)


PANEL_Y1=65; PANEL_Y2=918

MEDIA_DIR = resource_path("media")
PHOTOS_DIR = os.path.join(MEDIA_DIR, "photos")
CUBE_IMG_PATH = os.path.join(MEDIA_DIR, "kubik.png")
CUBE_VIDEO_PATH = os.path.join(MEDIA_DIR, "kubik.webm")
VOICEOVER_DIR = os.path.join(MEDIA_DIR, "voiceover")

# Recorded narration: file name, start offset (ms), end offset (ms).
# Offsets and durations were measured from the supplied .ogg paragraphs.
PHASE_AUDIO = {
    "step1":     ("01_resistors.wav",     0, 16294),
    "step2":     ("02_meters.wav",        0, 10854),
    "step3":     ("03_source.wav",        0,  7434),
    "step4":     ("04_circuit.wav",       0, 15573),
    "step5":     ("05_readings.wav",      0, 23453),
    "step6":     ("06_properties.wav",    0, 42974),
    "step6_p3":  ("07_equivalent.wav",    0, 24974),
    "step7":     ("08_r2_change.wav",     0, 16694),
}

# The last phase keeps running after its track ends: the R2 values are shown
# one after another and the summary panel appears at the end.
PHASE_DURATIONS_BY_KEY = {
    key: (end - start) + 300 for key, (_, start, end) in PHASE_AUDIO.items()
}
PHASE_DURATIONS_BY_KEY["step7"] = 24000

SW = []
def w(x1,y1,x2,y2): SW.append((x1+DX,y1+DY,x2+DX,y2+DY))
w(325,363, 419,363)
w(419,363, 506,363)
w(506,363, 693,363)
w(813,363, 993,363)
w(1113,363, 1200,363)
w(1200,363, 1200,575)
w(1200,575, 1200,790)
w(1200,790, 800,790)
w(800,790, 325,790)

BW = []
def b(x1,y1,x2,y2): BW.append((x1+DX,y1+DY,x2+DX,y2+DY))
b(600,363, 600,500)
b(600,500, 728,500)
b(773,500, 900,500)
b(900,500, 900,363)
b(900,363, 900,588)
b(900,588, 1028,588)
b(1073,588, 1200,588)
b(1200,588, 1200,363)
b(600,363, 600,713)
b(600,713, 878,713)
b(923,713, 1200,713)
b(1200,713, 1200,363)

# Узловые точки только в местах подключения приборов к общей цепи
# Всего 6 точек: 3 ветви вольтметров + точки подключения на основной магистрали
JUNCTION_DOTS = [
    (600+DX, 500+DY),   # T1: подключение PV1 к ветви (выход из ветви на магистраль/ответвление)
    (900+DX, 500+DY),   # T2: подключение PV1 (второй вывод)
    (900+DX, 363+DY),   # T3: подключение PV2 к общей цепи (на основной магистрали между R1 и R2)
    (1200+DX, 588+DY),  # T4: подключение PV2 к общей цепи
    (600+DX, 363+DY),   # T5: подключение PV3 к общей цепи (на магистрали после амперметра/перед R1)
    (1200+DX, 713+DY),  # T6: подключение PV3 к общей цепи
]

ALL_WIRE_STEPS = SW + BW

_REF_SCALE = 4/3

# --- Timed events inside a phase ---------------------------------------------
# t_ms is measured from the beginning of that phase's audio track.  Every event
# may reveal canvas tags and/or run a named action (formula/highlight switch).
PROPERTY1_TEXT = (
    "Первое свойство: общее напряжение равно сумме напряжений на всех "
    "последовательно соединённых участках: 4 + 8 = 12 В."
)
PROPERTY2_TEXT = (
    "Второе свойство: напряжение распределяется по участкам прямо "
    "пропорционально их сопротивлениям: R2/R1 = U2/U1 = 2."
)
SUMMARY_TEXT = (
    "Свойства последовательного соединения: U = U1 + U2;  Rэкв = R1 + R2;  "
    "I = U / (R1 + R2);  R2/R1 = U2/U1."
)

SUB_PHASE_GROUPS = {
    "step1": [
        {"t_ms": 10050, "tags": ["r1"]},   # «Первый резистор…»
        {"t_ms": 13200, "tags": ["r2"]},   # «Второй резистор…»
    ],
    "step2": [
        {"t_ms": 7250, "tags": ["pa1"]},                    # «миллиамперметр…»
        {"t_ms": 8750, "tags": ["pv1", "pv2", "pv3"]},      # «…и три вольтметра»
    ],
    "step3": [
        {"t_ms": 3600, "tags": ["e1", "e1_wire", "battery_photo"]},
    ],
    "step5": [
        {"t_ms": 5300,  "tags": []},            # R2 = 200 Ом
        {"t_ms": 9900,  "tags": ["pa1_val"]},   # 40 мА
        {"t_ms": 14800, "tags": ["pv1_val"]},   # 4 В
        {"t_ms": 19300, "tags": ["pv2_val"]},   # 8 В
        {"t_ms": 21700, "tags": ["pv3_val"]},   # 12 В
    ],
    "step6": [
        {"t_ms": 7320,  "action": "property1", "text": PROPERTY1_TEXT},
        {"t_ms": 20000, "action": "property2", "text": PROPERTY2_TEXT},
    ],
    "step7": [
        {"t_ms": 0,     "action": "r2_150"},
        {"t_ms": 4200,  "action": "r2_100"},
        {"t_ms": 7800,  "action": "r2_50"},
        {"t_ms": 11200, "action": "r2_25"},
        {"t_ms": 14600, "action": "r2_0"},
        {"t_ms": 17800, "action": "summary", "text": SUMMARY_TEXT},
    ],
}

class ResistorCartoon:
    def __init__(self, root):
        self.root = root
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self._scale = min(sw / 1600.0, (sh - 40) / 1050.0)
        self.px2 = int(sw / self._scale)
        self.px1 = self.px2 - 550
        self.root.title("Последовательное соединение резисторов - обучающий видеоурок")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.state("zoomed")
        self.root.resizable(False, False)

        self.paused      = False
        self.stopped     = True
        self.phase_idx   = 0
        self.phase_timer = None
        self.wire_timer  = None
        self.phase_start = 0.0
        self.phase_remaining = 0
        self.wire_substep = 0
        self.wire_in_progress = False
        self._schedule_time = 0
        self._timer_update_id = None
        self._junction_hl_timers = []
        self._junction_hl_items = []
        self.wires_visible = 0
        self.active_phases = set()
        self.active_sub_groups = {}  # phase_key -> set of sub_indices visible
        self._sub_phase_timers = []  # list of (after_id, deadline, phase_key, sub_idx)
        self._sub_phase_remaining = []  # list of (remaining_ms, phase_key, sub_idx) saved during pause
        self._in_transition = False  # True during the gap between phases

        self.phase_items = {}
        self.wire_items  = []
        self.formula_items = []
        self.f7_row_items = []
        self.photo_items = []
        self.cube_items = []
        self.speech_items = []

        self.narrator = AudioPlayer()
        self._speech_delay_id = None
        self.pa1_needle = None
        self.pv1_needle = None
        self.pv2_needle = None
        self.pv3_needle = None

        # Video playback state
        self._video_cap = None
        self._video_playing = False
        self._video_after_id = None
        self._video_poster = None  # static PhotoImage for pause

        self.setup_ui()
        self.load_images()
        self.create_circuit()
        self.create_component_photos()
        self.create_cube_character()
        s = self._scale
        self.canvas.scale("all", 0, 0, s, s)
        if hasattr(self, 'speech_text'):
            self.canvas.itemconfig(self.speech_text, width=max(1, int(576 * s)))
        self.canvas.config(width=int(self.px2 * s), height=int(920 * s))
        self.hide_all()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=C_BG)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            self.main_frame, bg=C_BG, width=1600, height=920,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.ctrl = tk.Frame(self.root, bg="#37474F", height=max(1, int(130 * self._scale)))
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X)
        self.ctrl.pack_propagate(False)

        btnf = tk.Frame(self.ctrl, bg="#37474F")
        btnf.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(8, 2))
        _bf = ("Arial", max(1, int(14 * self._scale)), "bold")
        _bf2 = ("Arial", max(1, int(14 * self._scale)))
        self.btn_play = tk.Button(
            btnf, text="  \u25b6 СТАРТ  ", font=_bf,
            command=self.on_play, bg="#43A047", fg="white",
            bd=0, padx=18, pady=4, cursor="hand2"
        )
        self.btn_play.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_pause = tk.Button(
            btnf, text="  \u23f8 ПАУЗА  ", font=_bf2,
            command=self.on_pause, bg="#FB8C00", fg="white",
            bd=0, padx=18, pady=4, cursor="hand2", state="disabled"
        )
        self.btn_pause.pack(side=tk.LEFT, padx=6)
        self.btn_reset = tk.Button(
            btnf, text="  \u21ba СБРОС  ", font=_bf2,
            command=self.on_reset, bg="#E53935", fg="white",
            bd=0, padx=18, pady=4, cursor="hand2", state="disabled"
        )
        self.btn_reset.pack(side=tk.LEFT, padx=6)

        step_names = [s[2] for s in self.PHASES]
        self.step_combo = ttk.Combobox(
            btnf, values=step_names, font=_bf2,
            state="readonly", width=45
        )
        self.step_combo.pack(side=tk.LEFT, padx=(20, 0))
        self.step_combo.set("Выберите шаг...")
        self.step_combo.bind("<<ComboboxSelected>>", self.on_step_selected)

        infof = tk.Frame(self.ctrl, bg="#37474F")
        infof.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(2, 8))
        self.prog = tk.Canvas(infof, height=max(1, int(14 * self._scale)), bg="#546E7A", highlightthickness=0)
        self.prog.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        self.step_label = tk.Label(
            infof, text="", font=("Consolas", max(1, int(12 * self._scale))),
            bg="#37474F", fg="#B0BEC5", width=20, anchor="w"
        )
        self.step_label.pack(side=tk.LEFT, padx=(0, 12))
        self.timer_label = tk.Label(
            infof, text="", font=("Consolas", max(1, int(14 * self._scale)), "bold"),
            bg="#37474F", fg="#FFF", width=8, anchor="e"
        )
        self.timer_label.pack(side=tk.RIGHT, padx=(0, 4))
        self.status_label = tk.Label(
            self.ctrl,
            text="Нажмите «СТАРТ» для начала",
            font=("Arial", max(1, int(13 * self._scale))), bg="#37474F", fg="#ECEFF1", anchor="w"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 4))
        self.prog_bg = self.prog.create_rectangle(0,0,2000,20, fill="#546E7A", outline="")
        self.prog_fill = self.prog.create_rectangle(0,0,0,20, fill="#66BB6A", outline="")

    def load_images(self):
        self.photo_imgs = {}
        sizes = {"resistor":(130, 90), "battery":(150, 240), "voltmeter":(90, 90), "ampermetr":(90, 90)}
        rotate_names = {"battery": -90}
        for name in ["resistor","battery","voltmeter","ampermetr"]:
            p = os.path.join(PHOTOS_DIR, name + ".png")
            try:
                pil = Image.open(p).convert("RGBA")
                pil = pil.resize(sizes[name], Image.LANCZOS)
                if name in rotate_names:
                    pil = pil.rotate(rotate_names[name], expand=True, fillcolor=(0,0,0,0))
                self.photo_imgs[name] = ImageTk.PhotoImage(pil)
            except:
                try:
                    img = tk.PhotoImage(file=p)
                    self.photo_imgs[name] = img
                except:
                    self.photo_imgs[name] = None

    def draw_resistor(self, x1, y, x2, label, tag, r2_mode=False):
        h = 28
        items = []
        cx = (x1 + x2) // 2
        img = self.photo_imgs.get("resistor")
        if img:
            items.append(self.canvas.create_image(cx, y, image=img, anchor="center", tags=tag))
        else:
            items.append(self.canvas.create_rectangle(
                x1, y-h, x2, y+h, fill=C_RESISTOR_BG, outline=C_RESISTOR, width=2, tags=tag
            ))
            w = x2 - x1
            pts = [x1, y]
            for i in range(1, 10, 2):
                pts.extend([x1 + i*w/10,   y - h + 5])
                pts.extend([x1 + (i+1)*w/10, y + h - 5])
            pts.extend([x2, y])
            items.append(self.canvas.create_line(*pts, fill=C_RESISTOR, width=2, tags=tag))
        items.append(self.canvas.create_text(
            (x1+x2)//2, y+h+18, text=label,
            font=("Arial", self._sf(16), "bold"), fill=C_TEXT, anchor="n", tags=tag
        ))
        if r2_mode:
            items.append(self.canvas.create_text(
                x2+22, y, text="\u21c5", font=("Arial", self._sf(20), "bold"),
                fill=C_R2_ARROW, anchor="center", tags=tag
            ))
            val = self.canvas.create_text(
                (x1+x2)//2, y-h-18, text="R2 = 200 \u03a9",
                font=("Arial", self._sf(16), "bold"), fill=C_TEXT, anchor="s", tags=tag
            )
            items.append(val)
            self.r2_label = val
        return items

    def draw_meter(self, cx, cy, kind, label, tag, specific_tag=None):
        items = []
        t = (tag, specific_tag) if specific_tag else tag
        import math
        import numpy as np
        w2 = METER_W / 2.0
        h2 = METER_H / 2.0
        # Корпус прибора: прямоугольный лаб. прибор со скруглёнными углами
        items.append(self.canvas.create_rectangle(
            cx-w2, cy-h2, cx+w2, cy+h2,
            fill="#E8E8E8", outline=C_METER_BORDER, width=2, tags=t
        ))
        items.append(self.canvas.create_rectangle(
            cx-w2+3, cy-h2+3, cx+w2-3, cy+h2-3,
            fill="#FAFAFA", outline="#9E9E9E", width=1, tags=t
        ))
        # Заголовок с обозначением прибора
        items.append(self.canvas.create_text(
            cx, cy-h2+12, text="%s  \u00b7  %s" % (label, kind),
            font=("Arial", self._sf(10), "bold"), fill=C_TEXT,
            anchor="center", tags=t
        ))
        # Шкала (дуга над осью вращения стрелки)
        px, py = cx, cy + METER_PIVOT_DY
        if kind == "A":
            vmin, vmax = 0, 120
            label_step, med_step, min_step = 40, 20, 10
        else:
            vmin, vmax = 0, 15
            label_step, med_step, min_step = 5, 1, 1
        span = vmax - vmin if vmax > vmin else 1
        a0, a1 = METER_ANG0, METER_ANG1
        for val in np.arange(vmin, vmax + 1e-6, min_step):
            a = a0 + (val - vmin) / span * (a1 - a0)
            rad = math.radians(a)
            near_max = abs(val - vmax) < 1e-4
            is_label = near_max or abs(val % label_step) < 1e-4
            is_med = (not is_label) and abs(val % med_step) < 1e-4
            if is_label:
                r1s, r2s, wdt = METER_RARC, METER_RARC-9, 2
            elif is_med:
                r1s, r2s, wdt = METER_RARC, METER_RARC-6, 1
            else:
                r1s, r2s, wdt = METER_RARC, METER_RARC-4, 1
            items.append(self.canvas.create_line(
                px + r1s*math.cos(rad), py + r1s*math.sin(rad),
                px + r2s*math.cos(rad), py + r2s*math.sin(rad),
                fill="#424242", width=wdt, tags=t
            ))
            if is_label:
                tr = METER_RARC - 17
                tx = px + tr * math.cos(rad)
                ty = py + tr * math.sin(rad)
                txt = "%d" % int(val) if abs(val - int(val)) < 1e-3 else "%g" % val
                items.append(self.canvas.create_text(
                    tx, ty, text=txt,
                    font=("Arial", self._sf(9), "bold"), fill=C_TEXT,
                    anchor="center", tags=t
                ))
        # Стрелка (в исходном положении — на нуле шкалы)
        za = math.radians(METER_ANG0)
        needle = self.canvas.create_line(
            px - METER_NEEDLE_TAIL*math.cos(za), py - METER_NEEDLE_TAIL*math.sin(za),
            px + METER_NEEDLE_LEN*math.cos(za), py + METER_NEEDLE_LEN*math.sin(za),
            fill="#D32F2F", width=3, tags=t
        )
        items.append(needle)
        items.append(self.canvas.create_oval(
            px-4, py-4, px+4, py+4, fill="#212121", outline="", tags=t
        ))
        # Цифровое показание: тёмный ЖК-экран под корпусом
        val_tags = (tag, specific_tag + "_val") if specific_tag else tag
        lcd_w = METER_W - 8
        lcd_h = 22
        lcd_top = cy + h2 + 2
        items.append(self.canvas.create_rectangle(
            cx-lcd_w/2, lcd_top, cx+lcd_w/2, lcd_top+lcd_h,
            fill="#1B1B1B", outline="#0D47A1", width=2, tags=val_tags
        ))
        val = self.canvas.create_text(
            cx, lcd_top + lcd_h/2, text="0.0",
            font=("Consolas", self._sf(12), "bold"), fill="#39FF6A",
            anchor="center", tags=val_tags
        )
        items.append(val)
        if specific_tag == "pa1":
            self.pa1_needle = needle
        elif specific_tag == "pv1":
            self.pv1_needle = needle
        elif specific_tag == "pv2":
            self.pv2_needle = needle
        elif specific_tag == "pv3":
            self.pv3_needle = needle
        return items, val

    def draw_battery(self, x, y1, y2, label, tag):
        items = []
        # GOST battery: thin (+) plate at top, thick short (−) plate at bottom
        items.append(self.canvas.create_line(x-20, y1, x+20, y1, fill=C_BATTERY, width=2, tags=tag))
        items.append(self.canvas.create_line(x-25, y2, x+25, y2, fill=C_BATTERY, width=6, tags=tag))
        # Polarity marks outside the battery, near circuit connection points
        items.append(self.canvas.create_text(
            x-38, y1, text="+", font=("Arial", self._sf(16), "bold"),
            fill=C_BATTERY, anchor="center", tags=tag
        ))
        items.append(self.canvas.create_text(
            x-38, y2, text="\u2212", font=("Arial", self._sf(16), "bold"),
            fill=C_BATTERY, anchor="center", tags=tag
        ))
        # Label between the plates
        items.append(self.canvas.create_text(
            x, (y1+y2)//2, text="E1 = " + label,
            font=("Arial", self._sf(14), "bold"), fill=C_TEXT,
            anchor="center", angle=90, tags=tag
        ))
        return items

    def junction_dot(self, x, y, tag):
        return self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=C_TEXT, outline="", tags=tag)

    def create_circuit(self):
        p = {}
        self.sub_phase_items = {}  # (phase_key, sub_idx) -> [items]

        p["step1"] = []
        r1_items = self.draw_resistor(R1_LEFT, R1_Y, R1_RIGHT, "R1 = 100 \u03a9", "r1")
        p["step1"].extend(r1_items)
        self.sub_phase_items[("step1", 0)] = r1_items

        r2_items = self.draw_resistor(R2_LEFT, R2_Y, R2_RIGHT, "R2 = 0\u2026200 \u03a9", "r2", r2_mode=True)
        p["step1"].extend(r2_items)
        self.sub_phase_items[("step1", 1)] = r2_items

        p["step2"] = []
        items, self.pa1_val = self.draw_meter(*PA1_CENTER, "A", "PA1", "meter", "pa1")
        p["step2"].extend(items)
        self.sub_phase_items[("step2", 0)] = items

        pv_items = []
        for label, center in [("PV1",PV1_CENTER),("PV2",PV2_CENTER),("PV3",PV3_CENTER)]:
            stag = label.lower()
            items, val = self.draw_meter(*center, "V", label, "meter", stag)
            pv_items.extend(items)
            p["step2"].extend(items)
            attr = {"PV1":"pv1_val","PV2":"pv2_val","PV3":"pv3_val"}[label]
            setattr(self, attr, val)
        self.sub_phase_items[("step2", 1)] = pv_items

        p["step3"] = []
        bx, by1, by2 = E1_X, E1_Y1, E1_Y2
        # GOST battery symbol (plates + polarity marks)
        bat_items = self.draw_battery(bx, by1, by2, "12 В", "e1")
        p["step3"].extend(bat_items)
        _, ty = N_TOP_LEFT
        _, by = N_BOT_LEFT
        # GOST: wires connect to the plates (no overlap into cell gap)
        p["step3"].append(self.canvas.create_line(bx, ty, bx, by1, fill=C_WIRE_SERIES, width=3, tags="e1_wire"))
        p["step3"].append(self.canvas.create_line(bx, by2, bx, by, fill=C_WIRE_SERIES, width=3, tags="e1_wire"))

        p["step4"] = []
        for jx, jy in JUNCTION_DOTS:
            p["step4"].append(self.junction_dot(jx, jy, "junc"))

        self.wire_items = []
        for i, (x1,y1,x2,y2) in enumerate(ALL_WIRE_STEPS):
            is_br = i >= len(SW)
            col = C_WIRE_BRANCH if is_br else C_WIRE_SERIES
            w = 5 if not is_br else 3
            item = self.canvas.create_line(x1, y1, x2, y2, fill=col, width=w, tags="w%d" % i)
            self.wire_items.append(item)
        self.canvas.tag_raise("meter")
        self.canvas.tag_raise("junc")
        self.canvas.tag_raise("hl_junc")

        p["step5"] = []
        self.phase_items = p
        self.create_formula_panel()

    def _panel_inner(self):
        return self.px1 + 20, self.px2 - 20

    def _rounded_rect(self, x1, y1, x2, y2, r=12, **kwargs):
        """Canvas rectangle with softly rounded corners."""
        r = max(1, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
        pts = [
            x1 + r, y1,  x2 - r, y1,  x2, y1,  x2, y1 + r,
            x2, y2 - r,  x2, y2,  x2 - r, y2,  x1 + r, y2,
            x1, y2,  x1, y2 - r,  x1, y1 + r,  x1, y1,
        ]
        return self.canvas.create_polygon(
            pts, smooth=True, splinesteps=24, **kwargs
        )

    def create_formula_panel(self):
        """Right-hand reference panel: centred, card-based and easy to scan."""
        px1, px2 = self.px1, self.px2
        cx = (px1 + px2) // 2
        header_h = 60
        x1, x2 = self._panel_inner()

        fi = []
        fi.append(self.canvas.create_rectangle(
            px1, PANEL_Y1, px2, PANEL_Y2,
            fill=C_PANEL_BG, outline=C_PANEL_BORDER, width=2, tags="f_all"
        ))
        fi.append(self.canvas.create_rectangle(
            px1 + 2, PANEL_Y1 + 2, px2 - 2, PANEL_Y1 + header_h - 2,
            fill="#37474F", outline="", tags="f_all"
        ))
        fi.append(self.canvas.create_rectangle(
            px1 + 2, PANEL_Y1 + header_h - 5, px2 - 2, PANEL_Y1 + header_h - 1,
            fill="#FFB300", outline="", tags="f_all"
        ))
        fi.append(self.canvas.create_text(
            cx, PANEL_Y1 + 31, text="СВОЙСТВА ЦЕПИ",
            font=("Arial", self._sf(21), "bold"), fill="#FFFFFF",
            anchor="center", tags="f_all"
        ))
        self.f_subtitle = self.canvas.create_text(
            cx, PANEL_Y1 + header_h + 24, text="",
            font=("Arial", self._sf(14)), fill="#607D8B",
            anchor="center", tags="f_all"
        )
        fi.append(self.f_subtitle)
        self.f_panel_bg_items = fi
        self.formula_items.extend(fi)

        # --- Step 5: measured values as a centred 2x3 card grid -------------
        self.f5_items = []
        self.f5_cards = []
        card_gap = 14
        card_w = (x2 - x1 - card_gap) // 2
        card_h = 128
        card_top = 174
        values = [
            ("R\u2081  ·  резистор 1", "100 Ом"),
            ("R\u2082  ·  резистор 2", "200 Ом"),
            ("I  ·  сила тока", "40 мА"),
            ("U\u2081  ·  напряжение", "4,0 В"),
            ("U\u2082  ·  напряжение", "8,0 В"),
            ("Uобщ  ·  напряжение", "12 В"),
        ]
        for i, (label, value) in enumerate(values):
            col, row = i % 2, i // 2
            cx1 = x1 + col * (card_w + card_gap)
            cy1 = card_top + row * (card_h + card_gap)
            cx2, cy2 = cx1 + card_w, cy1 + card_h
            ccx = (cx1 + cx2) // 2
            bg = self._rounded_rect(
                cx1, cy1, cx2, cy2, r=12,
                fill="#F7F9FA", outline="#DFE6EA", width=1, tags="f_step5"
            )
            lab = self.canvas.create_text(
                ccx, cy1 + 38, text=label,
                font=("Arial", self._sf(14)), fill="#607D8B",
                anchor="center", tags="f_step5"
            )
            val = self.canvas.create_text(
                ccx, cy1 + 84, text=value,
                font=("Arial", self._sf(26), "bold"), fill=C_TEXT,
                anchor="center", tags="f_step5"
            )
            self.f5_items.extend([bg, lab, val])
            self.f5_cards.append({"bg": bg, "label": lab, "value": val})

        sy1, sy2 = 614, 786
        sbg = self._rounded_rect(
            x1, sy1, x2, sy2, r=14,
            fill="#F1F8E9", outline="#C5E1A5", width=1, tags="f_step5"
        )
        st = self.canvas.create_text(
            cx, sy1 + 33, text="Проверка по закону Ома",
            font=("Arial", self._sf(15), "bold"), fill="#2E7D32",
            anchor="center", tags="f_step5"
        )
        s1 = self.canvas.create_text(
            cx, sy1 + 80,
            text="I = Uобщ / (R\u2081 + R\u2082) = 12 / 300 = 0,04 А",
            font=("Arial", self._sf(17)), fill=C_TEXT,
            anchor="center", tags="f_step5"
        )
        s2 = self.canvas.create_text(
            cx, sy1 + 123,
            text="I = 40 мА;   U\u2081 + U\u2082 = 4 + 8 = 12 В",
            font=("Arial", self._sf(16), "bold"), fill="#37474F",
            anchor="center", tags="f_step5"
        )
        note = self.canvas.create_text(
            cx, 824, text="R\u2082 = 200 Ом — исходное состояние цепи",
            font=("Arial", self._sf(13), "italic"), fill="#78909C",
            anchor="center", tags="f_step5"
        )
        self.f5_items.extend([sbg, st, s1, s2, note])
        self.formula_items.extend(self.f5_items)

        # --- Step 6: three properties, progressively added as cards ----------
        self.f6_groups = []
        self.f6_cards = []
        f6_top = 168
        f6_h = 225
        f6_gap = 20
        properties = [
            ("U = U\u2081 + U\u2082", "12 В = 4 В + 8 В",
             "Общее напряжение равно сумме\nнапряжений на всех участках.",
             "#1565C0"),
            ("R\u2082 / R\u2081 = U\u2082 / U\u2081", "200 / 100 = 8 / 4 = 2",
             "Напряжения распределяются прямо\nпропорционально сопротивлениям.",
             "#2E7D32"),
            ("Rэкв = R\u2081 + R\u2082", "Rэкв = 100 + 200 = 300 Ом",
             "Эквивалентное сопротивление\nравно сумме сопротивлений.",
             "#E65100"),
        ]
        for gi, (formula, value, desc, accent) in enumerate(properties):
            y1 = f6_top + gi * (f6_h + f6_gap)
            y2 = y1 + f6_h
            grp = []
            bg = self._rounded_rect(
                x1, y1, x2, y2, r=14,
                fill="#F7F9FA", outline="#DFE6EA", width=1, tags="f_step6"
            )
            grp.append(bg)
            grp.append(self.canvas.create_rectangle(
                x1 + 18, y1 + 2, x2 - 18, y1 + 6,
                fill=accent, outline="", tags="f_step6"
            ))
            grp.append(self.canvas.create_oval(
                x1 + 24, y1 + 24, x1 + 66, y1 + 66,
                fill=accent, outline="", tags="f_step6"
            ))
            grp.append(self.canvas.create_text(
                x1 + 45, y1 + 45, text=str(gi + 1),
                font=("Arial", self._sf(18), "bold"), fill="#FFFFFF",
                anchor="center", tags="f_step6"
            ))
            grp.append(self.canvas.create_text(
                x1 + 82, y1 + 45, text="СВОЙСТВО %d" % (gi + 1),
                font=("Arial", self._sf(14), "bold"), fill=accent,
                anchor="w", tags="f_step6"
            ))
            formula_item = self.canvas.create_text(
                cx, y1 + 92, text=formula,
                font=("Arial", self._sf(25), "bold"), fill="#C62828",
                anchor="center", tags="f_step6"
            )
            value_item = self.canvas.create_text(
                cx, y1 + 137, text=value,
                font=("Arial", self._sf(19)), fill=C_TEXT,
                anchor="center", tags="f_step6"
            )
            grp.append(formula_item)
            grp.append(value_item)
            grp.append(self.canvas.create_line(
                x1 + 34, y1 + 166, x2 - 34, y1 + 166,
                fill="#E0E6EA", width=1, tags="f_step6"
            ))
            grp.append(self.canvas.create_text(
                cx, y1 + 197, text=desc,
                font=("Arial", self._sf(15)), fill="#546E7A",
                anchor="center", justify="center", tags="f_step6"
            ))
            self.f6_groups.append(grp)
            self.f6_cards.append({
                "bg": bg, "formula": formula_item, "value": value_item
            })
            self.formula_items.extend(grp)
        self._f6_group_dy = [0, 0, 0]

        # --- Step 7: centred data table --------------------------------------
        self.f7_header = []
        self.f7_row_items = []
        self.f7_rows = []
        table_top = 176
        header_row_h = 44
        row_h = 58
        col_w = (x2 - x1) / 5.0
        col_cx = [x1 + col_w * (i + 0.5) for i in range(5)]
        self.f7_header.append(self._rounded_rect(
            x1, table_top, x2, table_top + header_row_h - 4,
            r=8, fill="#ECEFF1", outline="", tags="f_step7"
        ))
        for i, txt in enumerate(["R\u2082, Ом", "I, мА", "U\u2081, В", "U\u2082, В", "Uобщ, В"]):
            t = self.canvas.create_text(
                col_cx[i], table_top + (header_row_h - 4) / 2 - 1,
                text=txt, font=("Arial", self._sf(14), "bold"),
                fill="#37474F", anchor="center", tags="f_step7"
            )
            self.f7_header.append(t)
            self.formula_items.append(t)
        self.formula_items.extend(self.f7_header[:1])

        for ri, (r2, cur, u1, u2, utot) in enumerate([
            (200, 40, 4.0, 8.0, 12), (150, 48, 4.8, 7.2, 12),
            (100, 60, 6.0, 6.0, 12), (50,  80, 8.0, 4.0, 12),
            (25,  96, 9.6, 2.4, 12), (0,  120, 12.0, 0.0, 12),
        ]):
            ry1 = table_top + header_row_h + ri * row_h
            ry2 = ry1 + row_h - 4
            row_bg = self._rounded_rect(
                x1, ry1, x2, ry2, r=8,
                fill="#F7F9FA" if ri % 2 == 0 else "#FFFFFF",
                outline="", tags="f_step7"
            )
            cells = []
            row_vals = [
                str(r2), str(cur), ("%.1f" % u1).replace(".", ","),
                ("%.1f" % u2).replace(".", ","), str(utot)
            ]
            for ci, txt in enumerate(row_vals):
                t = self.canvas.create_text(
                    col_cx[ci], (ry1 + ry2) / 2, text=txt,
                    font=("Arial", self._sf(19)), fill=C_TEXT,
                    anchor="center", tags="f_step7"
                )
                cells.append(t)
                self.f7_row_items.append(t)
                self.formula_items.append(t)
            self.f7_rows.append({"bg": row_bg, "cells": cells})
            self.f7_row_items.append(row_bg)
            self.formula_items.append(row_bg)

        fy1, fy2 = 604, 776
        fbg = self._rounded_rect(
            x1, fy1, x2, fy2, r=14,
            fill="#E3F2FD", outline="#BBDEFB", width=1, tags="f_step7"
        )
        ft = self.canvas.create_text(
            cx, fy1 + 34, text="Как меняются показания",
            font=("Arial", self._sf(15), "bold"), fill="#1565C0",
            anchor="center", tags="f_step7"
        )
        f1 = self.canvas.create_text(
            cx, fy1 + 82, text="При увеличении R\u2082 ток уменьшается,",
            font=("Arial", self._sf(17)), fill=C_TEXT,
            anchor="center", tags="f_step7"
        )
        f2 = self.canvas.create_text(
            cx, fy1 + 120, text="U\u2081 растёт, U\u2082 падает, а U\u2081 + U\u2082 = 12 В",
            font=("Arial", self._sf(17), "bold"), fill="#37474F",
            anchor="center", tags="f_step7"
        )
        fnote = self.canvas.create_text(
            cx, 816,
            text="Сумма напряжений всегда равна напряжению источника.",
            font=("Arial", self._sf(13), "italic"), fill="#78909C",
            anchor="center", tags="f_step7"
        )
        self.f7_footer = [fbg, ft, f1, f2, fnote]
        self.formula_items.extend(self.f7_footer)

        # --- Step 8: four key properties as a clean summary ------------------
        self.f8_items = []
        self.f8_cards = []
        s_top = 168
        s_h = 168
        s_gap = 12
        summary = [
            ("U = U\u2081 + U\u2082", "Общее напряжение равно сумме\nнапряжений на участках.", "#1565C0"),
            ("Rэкв = R\u2081 + R\u2082", "Эквивалентное сопротивление\nравно сумме сопротивлений.", "#2E7D32"),
            ("I = U / (R\u2081 + R\u2082)", "Сила тока одинакова\nна всех участках цепи.", "#6A1B9A"),
            ("R\u2082 / R\u2081 = U\u2082 / U\u2081", "Напряжения пропорциональны\nсопротивлениям участков.", "#E65100"),
        ]
        for si, (formula, desc, accent) in enumerate(summary):
            y1 = s_top + si * (s_h + s_gap)
            y2 = y1 + s_h
            bg = self._rounded_rect(
                x1, y1, x2, y2, r=14,
                fill="#F7F9FA", outline="#DFE6EA", width=1, tags="f_step8"
            )
            strip = self.canvas.create_rectangle(
                x1 + 8, y1 + 20, x1 + 13, y2 - 20,
                fill=accent, outline="", tags="f_step8"
            )
            badge = self.canvas.create_oval(
                x1 + 24, y1 + 24, x1 + 60, y1 + 60,
                fill=accent, outline="", tags="f_step8"
            )
            num = self.canvas.create_text(
                x1 + 42, y1 + 42, text=str(si + 1),
                font=("Arial", self._sf(15), "bold"), fill="#FFFFFF",
                anchor="center", tags="f_step8"
            )
            form = self.canvas.create_text(
                cx, y1 + 62, text=formula,
                font=("Arial", self._sf(21), "bold"), fill="#C62828",
                anchor="center", tags="f_step8"
            )
            desc_item = self.canvas.create_text(
                cx, y1 + 115, text=desc,
                font=("Arial", self._sf(15)), fill="#546E7A",
                anchor="center", justify="center", tags="f_step8"
            )
            self.f8_items.extend([bg, strip, badge, num, form, desc_item])
            self.f8_cards.append({"bg": bg, "formula": form, "desc": desc_item})
        self.formula_items.extend(self.f8_items)

    def create_component_photos(self):
        img = self.photo_imgs.get("battery")
        if img:
            bx = E1_X - 120
            by = (E1_Y1 + E1_Y2) // 2
            item = self.canvas.create_image(bx, by, image=img, anchor="center", tags=("e1", "battery_photo"))
            if "step3" in self.phase_items:
                self.phase_items["step3"].append(item)

    def create_cube_character(self):
        cx, cy = 200, 740
        self._cube_pos = (cx, cy)

        # Try to load kubik.png as poster/fallback
        self._video_poster = None
        if os.path.exists(CUBE_IMG_PATH):
            try:
                pil = Image.open(CUBE_IMG_PATH).convert("RGBA")
                cs = max(1, round(502 * self._scale / _REF_SCALE))
                self._video_poster = ImageTk.PhotoImage(pil.resize((cs, cs), Image.LANCZOS))
            except:
                pass

        self.cube_img_id = self.canvas.create_image(
            cx, cy, image=self._video_poster, anchor="center", tags="cube"
        )
        self.cube_items.append(self.cube_img_id)

        # Open video
        self._open_video()

        # Speech bubble — larger, positioned to the right of cube
        bubble_x1 = cx + 140
        bubble_y1 = cy - 115
        bubble_x2 = cx + 740
        bubble_y2 = cy - 5
        self.speech_bg = self.canvas.create_rectangle(
            bubble_x1, bubble_y1, bubble_x2, bubble_y2,
            fill=C_SPEECH_BG, outline=C_SPEECH_BORDER, width=2,
            tags="speech"
        )
        self.speech_items.append(self.speech_bg)
        # Triangle pointer from bubble to cube
        tri_cx = cx + 85
        tri_y  = bubble_y2 + 2
        self.speech_tri = self.canvas.create_polygon(
            tri_cx, tri_y + 8,
            bubble_x1 - 2, tri_y - 4,
            bubble_x1 - 2, tri_y + 4,
            fill=C_SPEECH_BG, outline=C_SPEECH_BORDER, width=2,
            tags="speech"
        )
        self.speech_items.append(self.speech_tri)
        self.speech_text = self.canvas.create_text(
            (bubble_x1+bubble_x2)//2, (bubble_y1+bubble_y2)//2,
            text="", font=("Arial", self._sf(17)), fill=C_TEXT,
            anchor="center", width=int((bubble_x2 - bubble_x1) * 0.85), tags="speech"
        )
        self.speech_items.append(self.speech_text)
        self.canvas.tag_raise("speech")

    def _open_video(self):
        if self._video_cap:
            self._video_cap.release()
            self._video_cap = None
        if os.path.exists(CUBE_VIDEO_PATH):
            try:
                self._video_cap = cv2.VideoCapture(CUBE_VIDEO_PATH)
            except:
                self._video_cap = None

    def _video_update(self):
        if not self._video_playing or self.stopped:
            return
        if self._video_cap is None or not self._video_cap.isOpened():
            return
        ret, frame = self._video_cap.read()
        if not ret:
            # Loop the video
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._video_cap.read()
            if not ret:
                return
        try:
            frame_rgb = self._frame_to_rgba(frame)
            pil_img = Image.fromarray(frame_rgb, 'RGBA')
            cs = max(1, round(502 * self._scale / _REF_SCALE))
            pil_img = pil_img.resize((cs, cs), Image.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)
            self.canvas.itemconfig(self.cube_img_id, image=photo)
            self._video_current_photo = photo
        except:
            pass
        self._video_after_id = self.root.after(5, self._video_update)

    def _frame_to_rgba(self, bgr_frame):
        # Chroma key: remove pure black background (common in webm without alpha)
        is_bg = np.all(bgr_frame <= 8, axis=2)
        alpha = np.where(is_bg, 0, 255).astype(np.uint8)
        rgb = bgr_frame[...,::-1]
        return np.dstack((rgb, alpha))

    def _start_video(self):
        self._video_playing = True
        if self._video_cap is None or not self._video_cap.isOpened():
            self._open_video()
        if self._video_after_id:
            self.root.after_cancel(self._video_after_id)
            self._video_after_id = None
        self._video_update()

    def _stop_video(self):
        self._video_playing = False
        if self._video_after_id:
            self.root.after_cancel(self._video_after_id)
            self._video_after_id = None

    def hide_all(self):
        for lst in self.phase_items.values():
            for item in lst:
                self.canvas.itemconfig(item, state="hidden")
        for item in self.wire_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.formula_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.photo_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.cube_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.speech_items:
            self.canvas.itemconfig(item, state="hidden")
        self.wires_visible = 0
        self.active_phases.clear()
        self.active_sub_groups.clear()
        # Cancel any pending sub-phase timers
        for tid, _, _, _ in self._sub_phase_timers:
            self.root.after_cancel(tid)
        self._sub_phase_timers.clear()
        self._sub_phase_remaining.clear()

    def show_photo_panel(self, visible=True):
        state = "normal" if visible else "hidden"
        for item in self.photo_items:
            self.canvas.itemconfig(item, state=state)

    def show_cube(self, visible=True):
        state = "normal" if visible else "hidden"
        for item in self.cube_items:
            self.canvas.itemconfig(item, state=state)
        if visible:
            if not self._video_playing:
                self._start_video()
        else:
            self._stop_video()

    def show_speech(self, text):
        state = "normal"
        for item in self.speech_items:
            self.canvas.itemconfig(item, state=state)
        if hasattr(self, 'speech_text'):
            self.canvas.itemconfig(self.speech_text, text=text)

    def hide_speech(self):
        for item in self.speech_items:
            self.canvas.itemconfig(item, state="hidden")

    def _activate_sub_group(self, phase_key, sub_idx):
        groups = SUB_PHASE_GROUPS.get(phase_key, [])
        event = groups[sub_idx] if 0 <= sub_idx < len(groups) else {}

        action = event.get("action")
        if action == "property1":
            self.show_formula("step6_p1")
            self.show_speech(event.get("text", PROPERTY1_TEXT))
            self.highlight_property1()
        elif action == "property2":
            self.show_formula("step6_p2")
            self.show_speech(event.get("text", PROPERTY2_TEXT))
            self.highlight_property2()
        elif action and action.startswith("r2_"):
            r2 = int(action[3:])
            self.update_readings(r2)
            self.highlight_r2_table_row({150: 1, 100: 2, 50: 3, 25: 4, 0: 5}.get(r2, 0))
            self.highlight_junction_points(True)
        elif action == "summary":
            self._clear_formula_highlights()
            self.show_formula("step8")
            self.show_speech(event.get("text", SUMMARY_TEXT))
            self.highlight_junction_points(False)
        elif event.get("text"):
            self.show_speech(event["text"])

        if phase_key in self.active_sub_groups:
            self.active_sub_groups[phase_key].add(sub_idx)
        self._highlight_formula_data(phase_key, sub_idx)
        try:
            self.refresh_display()
        except Exception:
            pass

    def refresh_display(self):
        # Hide all phase items first
        for lst in self.phase_items.values():
            for item in lst:
                self.canvas.itemconfig(item, state="hidden")

        # Show items for fully active phases (legacy path)
        for key in self.active_phases:
            if key in self.phase_items:
                for item in self.phase_items[key]:
                    self.canvas.itemconfig(item, state="normal")

        # Show items for active sub-groups
        for phase_key, sub_indices in self.active_sub_groups.items():
            for sub_idx in sub_indices:
                key = (phase_key, sub_idx)
                if key in self.sub_phase_items:
                    for item in self.sub_phase_items[key]:
                        self.canvas.itemconfig(item, state="normal")
                else:
                    # Fallback: show items by tags
                    if phase_key in SUB_PHASE_GROUPS and sub_idx < len(SUB_PHASE_GROUPS[phase_key]):
                        tags = SUB_PHASE_GROUPS[phase_key][sub_idx].get("tags", [])
                        for tag in tags:
                            for item in self.canvas.find_withtag(tag):
                                self.canvas.itemconfig(item, state="normal")

        for i, item in enumerate(self.wire_items):
            state = "normal" if i < self.wires_visible else "hidden"
            self.canvas.itemconfig(item, state=state)
        if self.phase_idx > 0 or self.active_phases or self.active_sub_groups:
            self.show_photo_panel(True)
        self.show_cube(True)

    def _set_panel_subtitle(self, key):
        captions = {
            "step5": "Показания приборов при R\u2082 = 200 Ом",
            "step6_p1": "Свойство 1  ·  сумма напряжений",
            "step6_p2": "Свойство 2  ·  пропорциональность",
            "step6_p3": "Свойство 3  ·  эквивалентное сопротивление",
            "step7": "Зависимость показаний от R\u2082",
            "step8": "Итог  ·  четыре свойства соединения",
        }
        self.canvas.itemconfig(
            self.f_subtitle,
            text=captions.get(key, "Справочные данные по цепи"),
        )

    def _layout_f6_cards(self, count):
        """Keep the visible property cards vertically centred in the panel."""
        top, h, gap = 168, 225, 20
        available = 900 - top
        total = count * h + max(0, count - 1) * gap
        start = top + max(0, (available - total) // 2)
        for i in range(len(self.f6_groups)):
            target = start + i * (h + gap)
            base = top + i * (h + gap)
            delta = target - base
            shift = (delta - self._f6_group_dy[i]) * self._scale
            if shift:
                for item in self.f6_groups[i]:
                    self.canvas.move(item, 0, shift)
            self._f6_group_dy[i] = delta

    def show_formula(self, key):
        for item in self.formula_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.f_panel_bg_items:
            self.canvas.itemconfig(item, state="normal")
        self._set_panel_subtitle(key)
        if key == "step5":
            for item in self.f5_items:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p1":
            self._layout_f6_cards(1)
            for item in self.f6_groups[0]:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p2":
            # Keep property 1 on screen and add property 2 below it.
            self._layout_f6_cards(2)
            for gi in (0, 1):
                for item in self.f6_groups[gi]:
                    self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p3":
            self._layout_f6_cards(3)
            for grp in self.f6_groups:
                for item in grp:
                    self.canvas.itemconfig(item, state="normal")
        elif key == "step7":
            for item in self.f7_header:
                self.canvas.itemconfig(item, state="normal")
            for item in self.f7_row_items:
                self.canvas.itemconfig(item, state="normal")
            for item in self.f7_footer:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step8":
            for item in self.f8_items:
                self.canvas.itemconfig(item, state="normal")

    def calc_values(self, r2):
        r_total = 100.0 + r2
        i = 12.0 / r_total if r_total > 0 else 12.0 / 100.0
        return i, i*100.0, i*r2

    def update_readings(self, r2):
        import math
        i, u1, u2 = self.calc_values(r2)
        i_ma = i * 1000
        self.canvas.itemconfig(self.pa1_val, text="%d мА" % int(round(i_ma)))
        self.canvas.itemconfig(self.pv1_val, text="%.1f В" % u1)
        self.canvas.itemconfig(self.pv2_val, text="%.1f В" % u2)
        self.canvas.itemconfig(self.pv3_val, text="%.1f В" % (u1+u2))
        if hasattr(self, "r2_label"):
            self.canvas.itemconfig(self.r2_label, text="R2 = %d \u03a9" % r2)
        for needle, center, kind, v in [
            (getattr(self, 'pa1_needle', None), PA1_CENTER, "A", i_ma),
            (getattr(self, 'pv1_needle', None), PV1_CENTER, "V", u1),
            (getattr(self, 'pv2_needle', None), PV2_CENTER, "V", u2),
            (getattr(self, 'pv3_needle', None), PV3_CENTER, "V", u1+u2),
        ]:
            if needle is None:
                continue
            a = math.radians(_meter_angle(kind, v))
            ca, sa = math.cos(a), math.sin(a)
            px = center[0]
            py = center[1] + METER_PIVOT_DY
            s = self._scale
            self.canvas.coords(
                needle,
                (px - METER_NEEDLE_TAIL * ca) * s, (py - METER_NEEDLE_TAIL * sa) * s,
                (px + METER_NEEDLE_LEN * ca) * s, (py + METER_NEEDLE_LEN * sa) * s,
            )

    PHASES = [
        ("step1",       "Шаг 1 из 8","Появление резисторов R1 = 100 Ом и R2 = 0\u2026200 Ом"),
        ("step2",       "Шаг 2 из 8","Добавление измерительных приборов PA1, PV1\u2013PV3"),
        ("step3",       "Шаг 3 из 8","Подключение источника E1 = 12 В"),
        ("step4",       "Шаг 4 из 8","Сборка цепи: последовательное соединение"),
        ("step5",       "Шаг 5 из 8","Показания приборов при R2 = 200 Ом"),
        ("step6",       "Шаг 6 из 8","Свойства 1 и 2: U = U\u2081 + U\u2082, R\u2082/R\u2081 = U\u2082/U\u2081"),
        ("step6_p3",    "Шаг 7 из 8","Свойство 3: Rэкв = R\u2081 + R\u2082 = 300 Ом"),
        ("step7",       "Шаг 8 из 8","Изменение R2: ток растёт, напряжения перераспределяются"),
    ]
    PHASE_DURATIONS = [PHASE_DURATIONS_BY_KEY[p[0]] for p in PHASES]
    PHASE_FORMULA = [
        None,
        None, None, None, "step5",
        None,
        "step6_p3",
        "step7",
    ]

    def enter_phase(self, idx):
        if idx >= len(self.PHASES):
            self.show_final()
            return

        self.phase_idx = idx
        key, step_txt, status = self.PHASES[idx]
        dur = self.PHASE_DURATIONS[idx]

        self.step_label.config(text=step_txt)
        self.status_label.config(text=status)
        self.update_progress(idx)

        if self._speech_delay_id:
            self.root.after_cancel(self._speech_delay_id)
            self._speech_delay_id = None

        # Show the speech-bubble text and start the recorded paragraph.
        speech = PHASE_SPEECH[idx] if idx < len(PHASE_SPEECH) else status
        self.show_speech(speech)
        audio = PHASE_AUDIO.get(key)
        if audio:
            self.narrator.play(os.path.join(VOICEOVER_DIR, audio[0]), audio[1])
        else:
            self.narrator.stop()

        # Cancel old sub-phase timers
        for tid, _, _, _ in self._sub_phase_timers:
            self.root.after_cancel(tid)
        self._sub_phase_timers.clear()
        self._sub_phase_remaining.clear()

        # Add all previous phases fully visible (all sub-groups if any)
        for i in range(idx):
            pk = self.PHASES[i][0]
            if pk in SUB_PHASE_GROUPS:
                # All sub-groups of previous phases are visible
                self.active_sub_groups[pk] = set(range(len(SUB_PHASE_GROUPS[pk])))
            elif pk in self.phase_items:
                self.active_phases.add(pk)

        # Phase-specific readings are prepared before the timed events fire.
        if key == "step5":
            self.update_readings(200)

        # Clear annotations left over from the previous phase.
        self.clear_highlights()

        # Formula panel for this phase (step6 starts empty and is filled by events).
        fkey = self.PHASE_FORMULA[idx]
        if fkey:
            self.show_formula(fkey)
        else:
            for item in self.formula_items:
                self.canvas.itemconfig(item, state="hidden")
            for item in self.f_panel_bg_items:
                self.canvas.itemconfig(item, state="normal")
            self._set_panel_subtitle(None)

        if key == "step6_p3":
            self.highlight_property3()
            self._highlight_formula_data("step6_p3", 0)

        # Schedule the current phase's timed events.
        if key in SUB_PHASE_GROUPS:
            groups = SUB_PHASE_GROUPS[key]
            if key not in self.active_sub_groups:
                self.active_sub_groups[key] = set()
            for sub_idx, sg in enumerate(groups):
                delay = int(sg.get("t_ms", 0))
                if delay <= 50:
                    self._activate_sub_group(key, sub_idx)
                else:
                    deadline = time.time() + delay / 1000.0
                    tid = self.root.after(delay, lambda k=key, si=sub_idx: self._activate_sub_group(k, si))
                    self._sub_phase_timers.append((tid, deadline, key, sub_idx))
        else:
            self.active_phases.add(key)

        self.refresh_display()

        if key == "step4":
            self.wire_substep = 0
            self.wire_in_progress = True
            self.wires_visible = 0
            self.refresh_display()
            # The narration starts describing the circuit at ~5 s; begin
            # drawing the series wires at that moment.
            if self.wire_timer:
                self.root.after_cancel(self.wire_timer)
            self.wire_timer = self.root.after(4800, self.advance_wires)
        else:
            self.wire_in_progress = False

        self.phase_start = time.time()
        self.phase_remaining = dur
        self.schedule_next(dur)

    def schedule_next(self, delay_ms):
        if self.phase_timer:
            self.root.after_cancel(self.phase_timer)
        if self._timer_update_id:
            self.root.after_cancel(self._timer_update_id)
            self._timer_update_id = None
        self._schedule_time = delay_ms
        self.phase_timer = self.root.after(delay_ms, self.on_timeout)
        self.timer_label.config(text="%dс" % (max(1, delay_ms//1000)))
        self._update_timer_display()

    def _update_timer_display(self):
        if self.paused or self.stopped or self.phase_timer is None:
            self._timer_update_id = None
            return
        elapsed = (time.time() - self.phase_start) * 1000
        remaining = max(0, self._schedule_time - elapsed)
        self.timer_label.config(text="%dс" % (max(1, remaining//1000)))
        self._timer_update_id = self.root.after(500, self._update_timer_display)

    def on_timeout(self):
        self.phase_timer = None
        # Clean up junction highlights
        self.highlight_junction_points(False)
        if self._in_transition:
            # Transition gap is over — actually enter the next phase
            self._in_transition = False
            try:
                self.enter_phase(self.phase_idx + 1)
            except Exception:
                pass
            return
        # Finish any in-progress wire animation
        if self.wire_in_progress:
            self.wire_in_progress = False
            if self.wire_timer:
                self.root.after_cancel(self.wire_timer)
                self.wire_timer = None
            self.wires_visible = len(self.wire_items)
            try:
                self.refresh_display()
            except Exception:
                pass
        # Brief transition gap before next phase
        self._in_transition = True
        self.phase_remaining = 600
        self.phase_start = time.time()
        self.status_label.config(text="\u23ec")
        self.schedule_next(600)

    def advance_wires(self):
        if self.paused:
            return
        try:
            if self.wire_substep >= len(self.wire_items):
                self.wire_in_progress = False
                self.wires_visible = len(self.wire_items)
                return
            self.wire_substep += 1
            self.wires_visible = self.wire_substep
            self.refresh_display()
            if self.wire_substep < len(self.wire_items):
                # Draw the circuit over the whole explanatory paragraph.
                self.wire_timer = self.root.after(450, self.advance_wires)
            else:
                self.wire_in_progress = False
                self.wires_visible = len(self.wire_items)
        except Exception:
            self.wire_in_progress = False
            self.wires_visible = len(self.wire_items)

    def _sf(self, size):
        return max(1, round(size * self._scale / _REF_SCALE))

    def clear_highlights(self):
        self.highlight_junction_points(False)
        self._clear_formula_highlights()
        for item in self.canvas.find_withtag("hl"):
            self.canvas.delete(item)

    def _hl_frame(self, x1, y1, x2, y2, colour):
        s = self._scale
        self.canvas.create_rectangle(
            round((x1-6)*s), round((y1-6)*s), round((x2+6)*s), round((y2+6)*s),
            outline=colour, width=max(1, round(3*s)),
            dash=(round(6*s), round(3*s)), tags="hl"
        )

    def _hl_text(self, text, colour):
        s = self._scale
        self.canvas.create_text(
            round(800*s), round(790*s), text=text,
            font=("Arial", self._sf(18), "bold"), fill=colour,
            anchor="center", tags="hl"
        )

    def highlight_property1(self):
        self.clear_highlights()
        for cx,cy in [PV1_CENTER, PV2_CENTER, PV3_CENTER]:
            self._hl_frame(cx-52, cy-48, cx+52, cy+70, "#E65100")
        self._hl_text("U = U\u2081 + U\u2082 = 4 + 8 = 12 В", "#D32F2F")

    def highlight_property2(self):
        self.clear_highlights()
        self._hl_frame(R1_LEFT-10, R1_Y-32, R1_RIGHT+10, R1_Y+32, "#1565C0")
        self._hl_frame(R2_LEFT-10, R2_Y-32, R2_RIGHT+10, R2_Y+32, "#1565C0")
        self._hl_frame(PV1_CENTER[0]-52, PV1_CENTER[1]-48, PV1_CENTER[0]+52, PV1_CENTER[1]+70, "#2E7D32")
        self._hl_frame(PV2_CENTER[0]-52, PV2_CENTER[1]-48, PV2_CENTER[0]+52, PV2_CENTER[1]+70, "#2E7D32")
        self._hl_text("R\u2082/R\u2081 = U\u2082/U\u2081 = 200/100 = 8/4 = 2", "#1565C0")

    def highlight_property3(self):
        self.clear_highlights()
        self._hl_frame(R1_LEFT-10, R1_Y-32, R1_RIGHT+10, R1_Y+32, "#E65100")
        self._hl_frame(R2_LEFT-10, R2_Y-32, R2_RIGHT+10, R2_Y+32, "#E65100")
        self._hl_text("Rэкв = R\u2081 + R\u2082 = 100 + 200 = 300 Ом", "#E65100")

    def highlight_junction_points(self, visible=True):
        """Show black dots at voltmeter connection points to the main circuit."""
        for item in getattr(self, '_junction_hl_items', []):
            self.canvas.delete(item)
        self._junction_hl_items = []
        if not visible:
            return
        s = self._scale
        for jx, jy in JUNCTION_DOTS:
            dot = self.canvas.create_oval(
                (jx-8)*s, (jy-8)*s, (jx+8)*s, (jy+8)*s,
                fill="#212121", outline="", tags="hl_junc"
            )
            self._junction_hl_items.append(dot)
        self.canvas.tag_raise("speech")

    def _clear_formula_highlights(self):
        for item in self.canvas.find_withtag("f_hl"):
            self.canvas.delete(item)
        for card in getattr(self, "f5_cards", []):
            self.canvas.itemconfig(
                card["bg"], fill="#F7F9FA", outline="#DFE6EA", width=1
            )
        for card in getattr(self, "f6_cards", []):
            self.canvas.itemconfig(
                card["bg"], fill="#F7F9FA", outline="#DFE6EA", width=1
            )
        for ri, row in enumerate(getattr(self, "f7_rows", [])):
            self.canvas.itemconfig(
                row["bg"], fill="#F7F9FA" if ri % 2 == 0 else "#FFFFFF"
            )
            for cell in row["cells"]:
                self.canvas.itemconfig(
                    cell, fill=C_TEXT,
                    font=("Arial", self._sf(19), "normal")
                )

    def _highlight_formula_data(self, phase_key, sub_idx):
        if phase_key == "step5":
            self._clear_formula_highlights()
            # Data cards: R1, R2, I, U1, U2, Uобщ.  The narration highlights
            # R2, I, U1, U2 and Uобщ in that order.
            row_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
            ri = row_map.get(sub_idx)
            if ri is not None and ri < len(self.f5_cards):
                self.canvas.itemconfig(
                    self.f5_cards[ri]["bg"],
                    fill="#FFF8E1", outline="#FFB300", width=2
                )
        elif phase_key in ("step6", "step6_p1", "step6_p2", "step6_p3"):
            self._clear_formula_highlights()
            if phase_key == "step6":
                grp_idx = sub_idx
            else:
                grp_idx = {"step6_p1": 0, "step6_p2": 1, "step6_p3": 2}.get(phase_key, 0)
            if grp_idx < len(self.f6_cards):
                self.canvas.itemconfig(
                    self.f6_cards[grp_idx]["bg"],
                    fill="#EAF3FB", outline="#1565C0", width=2
                )

    def highlight_r2_table_row(self, row_idx):
        self._clear_formula_highlights()
        if not (0 <= row_idx < len(self.f7_rows)):
            return
        row = self.f7_rows[row_idx]
        self.canvas.itemconfig(row["bg"], fill="#E8F5E9")
        for cell in row["cells"]:
            self.canvas.itemconfig(
                cell, fill="#1B5E20",
                font=("Arial", self._sf(19), "bold")
            )

    def update_progress(self, idx):
        total = len(self.PHASES)
        frac = (idx + 1) / total if idx >= 0 else 0
        bw = max(self.prog.winfo_width() - 4, 400)
        fw = int(bw * frac)
        self.prog.coords(self.prog_fill, 2, 2, 2 + fw, 16)

    def on_play(self):
        if not self.stopped:
            return
        self.stopped = False
        self.paused = False
        self.btn_play.config(state="disabled")
        self.btn_pause.config(state="normal", text="  \u23f8 ПАУЗА  ")
        self.btn_reset.config(state="normal")
        self.show_photo_panel(True)
        self.show_cube(True)
        self.enter_phase(0)

    def on_pause(self):
        if self.stopped:
            return
        if not self.paused:
            self.paused = True
            self.btn_pause.config(text="  \u25b6 ПРОДОЛЖИТЬ  ")
            self.narrator.pause()
            self._stop_video()
            self._show_poster_frame()
            if self.phase_timer:
                self.root.after_cancel(self.phase_timer)
                self.phase_timer = None
            if self._timer_update_id:
                self.root.after_cancel(self._timer_update_id)
                self._timer_update_id = None
            if self.wire_timer:
                self.root.after_cancel(self.wire_timer)
                self.wire_timer = None
            if self._speech_delay_id:
                self.root.after_cancel(self._speech_delay_id)
                self._speech_delay_id = None
            # Save remaining time for sub-phase timers
            self._sub_phase_remaining.clear()
            for tid, deadline, key, sub_idx in self._sub_phase_timers:
                self.root.after_cancel(tid)
                remaining = max(0, (deadline - time.time()) * 1000)
                if remaining > 50:
                    self._sub_phase_remaining.append((remaining, key, sub_idx))
                else:
                    # Show immediately on resume if very close
                    self._sub_phase_remaining.append((0, key, sub_idx))
            self._sub_phase_timers.clear()
            elapsed = (time.time() - self.phase_start) * 1000
            self.phase_remaining = max(0, self.phase_remaining - elapsed)
            self.timer_label.config(text="\u23f8")
        else:
            self.paused = False
            self.btn_pause.config(text="  \u23f8 ПАУЗА  ")
            self.narrator.resume()
            self._start_video()  # Resume video
            self.phase_start = time.time()
            if self.wire_in_progress:
                self.wire_timer = self.root.after(50, self.advance_wires)
            # Restore sub-phase timers with adjusted delays
            for remaining, key, sub_idx in self._sub_phase_remaining:
                if remaining > 50:
                    deadline = time.time() + remaining / 1000.0
                    tid = self.root.after(int(remaining), lambda k=key, si=sub_idx: self._activate_sub_group(k, si))
                    self._sub_phase_timers.append((tid, deadline, key, sub_idx))
                else:
                    self._activate_sub_group(key, sub_idx)
            self._sub_phase_remaining.clear()
            self.schedule_next(int(self.phase_remaining))

    def on_close(self):
        try:
            self.narrator.stop()
        except Exception:
            pass
        self.root.destroy()

    def on_reset(self):
        self.stopped = True
        self.paused = False
        self.narrator.stop()
        self._stop_video()
        if self._video_cap:
            self._video_cap.release()
            self._video_cap = None
        if self.phase_timer:
            self.root.after_cancel(self.phase_timer)
            self.phase_timer = None
        if self._timer_update_id:
            self.root.after_cancel(self._timer_update_id)
            self._timer_update_id = None
        if self.wire_timer:
            self.root.after_cancel(self.wire_timer)
            self.wire_timer = None
        if self._speech_delay_id:
            self.root.after_cancel(self._speech_delay_id)
            self._speech_delay_id = None
        self.wire_in_progress = False
        # Cancel sub-phase timers
        for tid, _, _, _ in self._sub_phase_timers:
            self.root.after_cancel(tid)
        self._sub_phase_timers.clear()
        self._sub_phase_remaining.clear()
        self._in_transition = False
        self.clear_highlights()
        self.highlight_junction_points(False)
        self.hide_all()
        # Reset video to start
        self._open_video()
        self._show_poster_frame()
        self.btn_play.config(state="normal")
        self.btn_pause.config(state="disabled", text="  \u23f8 ПАУЗА  ")
        self.btn_reset.config(state="disabled")
        self.step_label.config(text="")
        self.status_label.config(text="Нажмите «СТАРТ» для начала")
        self.timer_label.config(text="")
        self.update_progress(-1)
        self.hide_speech()

    def on_step_selected(self, event):
        sel = self.step_combo.get()
        for idx, (_, _, s) in enumerate(self.PHASES):
            if s == sel:
                self.narrator.stop()
                self._stop_video()
                if self.phase_timer:
                    self.root.after_cancel(self.phase_timer)
                    self.phase_timer = None
                if self._timer_update_id:
                    self.root.after_cancel(self._timer_update_id)
                    self._timer_update_id = None
                if self.wire_timer:
                    self.root.after_cancel(self.wire_timer)
                    self.wire_timer = None
                if self._speech_delay_id:
                    self.root.after_cancel(self._speech_delay_id)
                    self._speech_delay_id = None
                for tid, _, _, _ in self._sub_phase_timers:
                    self.root.after_cancel(tid)
                self._sub_phase_timers.clear()
                self._sub_phase_remaining.clear()
                self._in_transition = False
                self.wire_in_progress = False
                self.clear_highlights()
                self.highlight_junction_points(False)
                self.hide_all()
                self.wires_visible = len(self.wire_items)
                self.stopped = False
                self.paused = False
                self.btn_play.config(state="disabled")
                self.btn_pause.config(state="normal", text="  \u23f8 ПАУЗА  ")
                self.btn_reset.config(state="normal")
                self.show_photo_panel(True)
                self.show_cube(True)
                self.enter_phase(idx)
                break

    def _show_poster_frame(self):
        if self._video_poster:
            self.canvas.itemconfig(self.cube_img_id, image=self._video_poster)
            self._video_current_photo = self._video_poster
        elif self._video_cap and self._video_cap.isOpened():
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._video_cap.read()
            if ret:
                try:
                    frame_rgba = self._frame_to_rgba(frame)
                    pil_img = Image.fromarray(frame_rgba, 'RGBA')
                    cs = max(1, round(502 * self._scale / _REF_SCALE))
                    pil_img = pil_img.resize((cs, cs), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    self.canvas.itemconfig(self.cube_img_id, image=photo)
                    self._video_current_photo = photo
                except:
                    pass

    def show_final(self):
        self.narrator.stop()
        self.status_label.config(
            text="Видеоурок завершён! Нажмите «СБРОС» для повтора."
        )
        self.timer_label.config(text="\u2714")
        self.step_label.config(text="Шаг 8 из 8")
        self.btn_pause.config(state="disabled")
        self._stop_video()
        self._show_poster_frame()
        if self._timer_update_id:
            self.root.after_cancel(self._timer_update_id)
            self._timer_update_id = None
        self.show_speech("Видеоурок завершён! Спасибо за внимание.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ResistorCartoon(root)
    root.mainloop()
