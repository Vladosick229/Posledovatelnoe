import sys
import tkinter as tk
from tkinter import ttk
import time
import threading
import os
import queue
import pythoncom
import win32com.client
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

class TTSManager:
    def __init__(self):
        self._queue = queue.Queue()
        self._voice = None
        self._start_worker()

    def _start_worker(self):
        def _worker():
            pythoncom.CoInitialize()
            try:
                v = win32com.client.Dispatch("SAPI.SpVoice")
                v.Rate = 3
                v.Volume = 100
                v.Speak("", 1)  # warm up engine to avoid first-word delay
                self._voice = v
                while True:
                    item = self._queue.get()
                    if item is None:
                        v = None
                        self._voice = None
                        break
                    text, callback = item
                    try:
                        v.Speak(text, 0)
                    except Exception:
                        pass
                    if callback:
                        callback()
            finally:
                pythoncom.CoUninitialize()
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def speak(self, text, callback=None):
        self._queue.put((text, callback))

    def estimate_ms(self, text):
        chars = len(text)
        return max(2500, chars * 55)

    def pause(self):
        if self._voice:
            try:
                self._voice.Pause()
            except Exception:
                pass

    def resume(self):
        if self._voice:
            try:
                self._voice.Resume()
            except Exception:
                pass

    def stop(self):
        self.resume()
        self._queue.queue.clear()

TIMINGS = {
    "step0_welcome":         6000,
    "step1_show_resistors": 4000,
    "step2_show_meters":    4000,
    "step3_show_battery":   3000,
    "step4_build_wires":    7000,
    "step5_initial_values": 7000,
    "step6_property1":      7000,
    "step6_property2":      7000,
    "step6_property3":      7000,
    "step7_r2_150":         5000,
    "step7_r2_100":         5000,
    "step7_r2_50":          5000,
    "step7_r2_25":          5000,
    "step7_r2_0":           5000,
    "step8_finish":         8000,
}

NARRATION = [
    "Здравствуйте! В этом видеоуроке мы познакомимся с последовательным соединением резисторов и его свойствами. Мы соберём электрическую цепь, проведём измерения и убедимся в справедливости законов последовательного соединения.",
    "Свойства последовательного соединения можно продемонстрировать с помощью несложного опыта. Для его проведения нам понадобятся два резистора: первый резистор с сопротивлением 100 Ом, второй резистор с переменным сопротивлением.",
    "Также для определения силы тока и напряжений будут использоваться электроизмерительные приборы: миллиамперметр и три вольтметра.",
    "Для получения экспериментальных данных будем использовать источник постоянного напряжения 12 Вольт.",
    "Собираем электрическую цепь с последовательным соединением резисторов. Следует помнить, что амперметр включается последовательно с элементами, ток через которые требуется измерить, а вольтметры включаются параллельно.",
    "Первоначально установим сопротивление переменного резистора R2 равным 200 Ом. При этом амперметр будет показывать силу тока 40 миллиампер, первый вольтметр показывает напряжение 4 Вольта, второй вольтметр показывает напряжение 8 Вольт, третий вольтметр показывает 12 Вольт.",
    "С помощью этих показаний подтверждается первое свойство последовательного соединения: общее напряжение равно сумме напряжений на всех последовательно соединенных участках, то есть 4 плюс 8 равно 12 Вольт.",
    "Второе свойство: общее напряжение распределяется по участкам прямо пропорционально их сопротивлениям. Сопротивление второго резистора в 2 раза больше сопротивления первого, поэтому напряжение на втором резисторе в два раза больше, чем на первом.",
    "По показаниям приборов, используя закон Ома, можно рассчитать сопротивление цепи. Оно будет равно 300 Ом. Эквивалентное сопротивление равно сумме сопротивлений всех последовательно соединенных участков: 100 плюс 200 равно 300 Ом.",
    "При уменьшении сопротивления одного из последовательно соединенных элементов сила тока в цепи увеличивается, при этом напряжения на участках изменяются, но их сумма равна общему напряжению. Уменьшаем R2 до 150 Ом.",
    "R2 равно 100 Ом. Ток растёт, напряжения U1 и U2 выравниваются.",
    "R2 равно 50 Ом. Ток значительно возрос, напряжение на втором резисторе стало меньше, чем на первом.",
    "R2 равно 25 Ом. Почти короткое замыкание: ток 96 миллиампер, напряжение U2 всего 2.4 Вольта.",
    "R2 равно 0 Ом. Короткое замыкание. Всё напряжение на первом резисторе. Ток 120 миллиампер.",
    "Повторим свойства последовательного соединения: общее напряжение равно сумме напряжений на участках, эквивалентное сопротивление равно сумме сопротивлений, ток в цепи определяется по закону Ома.",
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
PANEL_Y1=65; PANEL_Y2=925

MEDIA_DIR = resource_path("media")
PHOTOS_DIR = os.path.join(MEDIA_DIR, "photos")
CUBE_IMG_PATH = os.path.join(MEDIA_DIR, "kubik.png")
CUBE_VIDEO_PATH = os.path.join(MEDIA_DIR, "kubik.webm")

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
    (600+DX, 713+DY),   # T5: подключение PV3
    (1200+DX, 713+DY),  # T6: подключение PV3
]

ALL_WIRE_STEPS = SW + BW

_REF_SCALE = 4/3

# --- Sub-phase groups for sequential element revealing ---
# Each sub-group has a delay (ms from phase start) and a list of canvas tags to show
SUB_PHASE_GROUPS = {
    "step1": [
        {"trigger": "первый резистор", "tags": ["r1"]},
        {"trigger": "второй резистор", "tags": ["r2"]},
    ],
    "step2": [
        {"trigger": "миллиамперметр", "tags": ["pa1"]},
        {"trigger": "три вольтметра", "tags": ["pv1", "pv2", "pv3"]},
    ],
    "step3": [
        {"trigger": "источник постоянного", "tags": ["e1", "e1_wire", "battery_photo"]},
    ],
    "step5": [
        {"trigger": "200 Ом",      "tags": []},
        {"trigger": "40 миллиампер", "tags": ["pa1_val"]},
        {"trigger": "4 Вольта",     "tags": ["pv1_val"]},
        {"trigger": "8 Вольт",      "tags": ["pv2_val"]},
        {"trigger": "12 Вольт",     "tags": ["pv3_val"]},
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
        self._speech_ended = False
        self._speech_phase_idx = -1
        self._min_phase_dur_ms = 0
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

        self.tts = TTSManager()
        self._speech_delay_id = None

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
        img_key = "ampermetr" if kind == "A" else "voltmeter"
        img = self.photo_imgs.get(img_key)
        if img:
            items.append(self.canvas.create_image(cx, cy, image=img, anchor="center", tags=t))
            dy = 55
        else:
            r = 18
            items.append(self.canvas.create_oval(
                cx-r, cy-r, cx+r, cy+r,
                fill=C_METER_BG, outline=C_METER_BORDER, width=2, tags=t
            ))
            items.append(self.canvas.create_text(
                cx, cy, text=kind, font=("Arial", self._sf(16), "bold"),
                fill=C_TEXT, anchor="center", tags=t
            ))
            dy = 0
        items.append(self.canvas.create_text(
            cx, cy+dy+r+14 if not img else cy+48, text=label,
            font=("Arial", self._sf(11), "bold"), fill=C_TEXT, anchor="n", tags=t
        ))
        val_tags = (tag, specific_tag + "_val") if specific_tag else tag
        val = self.canvas.create_text(
            cx, cy+dy+r+32 if not img else cy+63, text="",
            font=("Consolas", self._sf(11)), fill="#D32F2F", anchor="n", tags=val_tags
        )
        items.append(val)
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

    def create_formula_panel(self):
        px = self.px1 + 20
        fy0 = PANEL_Y1 + 70
        fi = []
        fi.append(self.canvas.create_rectangle(
            self.px1, PANEL_Y1, self.px2, PANEL_Y2,
            fill=C_PANEL_BG, outline=C_PANEL_BORDER, width=2, tags="f_all"
        ))
        fi.append(self.canvas.create_text(
            (self.px1+self.px2)//2, PANEL_Y1+25,
            text="Свойства цепи",
            font=("Arial", self._sf(24), "bold"), fill=C_TABLE_HEADER,
            anchor="center", tags="f_all"
        ))
        self.f_panel_bg_items = fi
        self.formula_items.extend(fi)

        self.f5_items = []
        ty = fy0
        self.f5_items.append(self.canvas.create_text(
            px, ty,
            text="{:15}{:>8}".format("Параметр", "Значение"),
            font=("Consolas", self._sf(20), "bold"), fill=C_TABLE_HEADER,
            anchor="w", tags="f_step5"
        ))
        for i, (param, val) in enumerate([
            ("R1", "100 Ом"), ("R2", "200 Ом"),
            ("I", "40 мА"), ("U1", "4.0 В"),
            ("U2", "8.0 В"), ("Uобщ", "12 В"),
        ]):
            y = ty + 40 + i*36
            self.f5_items.append(self.canvas.create_text(
                px, y, text="{:15}{:>8}".format(param, val),
                font=("Consolas", self._sf(20)), fill=C_TEXT,
                anchor="w", tags="f_step5"
            ))
        self.formula_items.extend(self.f5_items)

        self.f6_groups = []
        for lines in [
            ["U = U\u2081 + U\u2082", "12 В = 4 В + 8 В",
             "Напряжение на участке равно", "сумме напряжений на",
             "отдельных резисторах."],
            ["R\u2082 / R\u2081 = U\u2082 / U\u2081", "200 / 100 = 8 / 4 = 2",
             "Сопротивления", "пропорциональны", "напряжениям."],
            ["R\u044d\u043a\u0432 = R\u2081 + R\u2082",
             "Rэкв = 100 + 200 = 300 Ом",
             "Эквивалентное", "сопротивление равно", "сумме сопротивлений."],
        ]:
            grp = []
            y0 = fy0
            for li, line in enumerate(lines):
                fs = self._sf(22 if li < 2 else 18)
                fw = "bold" if li < 2 else "normal"
                fc = "#D32F2F" if li < 2 else C_TEXT
                y = y0 + li*40 + len(self.f6_groups)*160
                grp.append(self.canvas.create_text(
                    px, y, text=line,
                    font=("Arial", fs, fw), fill=fc,
                    anchor="w", tags="f_step6"
                ))
            self.f6_groups.append(grp)
            for item in grp:
                self.formula_items.append(item)

        y7 = fy0
        # columns at fixed X positions for proper alignment (using Consolas monospace)
        col_x = [px + i*135 for i in range(5)]
        col_hdr = ["R2","I","U1","U2","Uобщ"]
        self.f7_header = []
        for i, txt in enumerate(col_hdr):
            t = self.canvas.create_text(
                col_x[i], y7, text=txt,
                font=("Arial", self._sf(22), "bold"), fill="#D32F2F",
                anchor="w", tags="f_step7"
            )
            self.f7_header.append(t)
            self.formula_items.append(t)
        self.f7_row_items = []
        for ri, (r2, i, u1, u2, utot) in enumerate([
            (200, 40, 4.0, 8.0, 12), (150, 48, 4.8, 7.2, 12),
            (100, 60, 6.0, 6.0, 12), (50,  80, 8.0, 4.0, 12),
            (25,  96, 9.6, 2.4, 12), (0,  120, 12.0, 0.0, 12),
        ]):
            y = y7 + 70 + ri*65
            row_vals = [str(r2), f"{i}мА", f"{u1:.1f}В", f"{u2:.1f}В", f"{utot:.0f}В"]
            for ci, txt in enumerate(row_vals):
                t = self.canvas.create_text(
                    col_x[ci], y, text=txt,
                    font=("Arial", self._sf(23)), fill=C_TEXT,
                    anchor="w", tags="f_step7"
                )
                self.f7_row_items.append(t)
                self.formula_items.append(t)

        self.f8_items = []
        for li, line in enumerate([
            "Свойства последовательного", "соединения резисторов:", "",
            "1.  U = U\u2081 + U\u2082",
            "    (общее напряжение = сумме)", "",
            "2.  Rэкв = R\u2081 + R\u2082",
            "    (эквивалентное сопротивление)", "",
            "3.  I = U / (R\u2081 + R\u2082)", "    (ток в цепи)", "",
            "4.  R\u2082 / R\u2081 = U\u2082 / U\u2081",
            "    (пропорциональность)",
        ]):
            is_numbered = line and line[0].isdigit()
            fs = self._sf(22 if is_numbered else 18)
            fw = "bold" if is_numbered else "normal"
            fc = "#D32F2F" if "=" in line else C_TEXT
            y = fy0 + li*34
            self.f8_items.append(self.canvas.create_text(
                px, y, text=line,
                font=("Arial", fs, fw), fill=fc,
                anchor="w", tags="f_step8"
            ))
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

    def _get_trigger_delay(self, phase_key, trigger):
        """Calculate delay in ms for a sub-phase trigger word within the narration text."""
        idx = next((i for i, (pk,_,_) in enumerate(self.PHASES) if pk == phase_key), None)
        if idx is None or idx >= len(NARRATION):
            return 0
        text = NARRATION[idx]
        pos = text.find(trigger)
        if pos < 0:
            return 0
        chars_before = len(text[:pos])
        total_chars = max(len(text), 1)
        total_dur = self.tts.estimate_ms(text)
        delay = int(total_dur * chars_before / total_chars)
        return max(0, delay - 600)  # slightly before the word is fully spoken

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
                        tags = SUB_PHASE_GROUPS[phase_key][sub_idx]["tags"]
                        for tag in tags:
                            for item in self.canvas.find_withtag(tag):
                                self.canvas.itemconfig(item, state="normal")

        for i, item in enumerate(self.wire_items):
            state = "normal" if i < self.wires_visible else "hidden"
            self.canvas.itemconfig(item, state=state)
        if self.phase_idx > 0 or self.active_phases or self.active_sub_groups:
            self.show_photo_panel(True)
        self.show_cube(True)

    def show_formula(self, key):
        for item in self.formula_items:
            self.canvas.itemconfig(item, state="hidden")
        for item in self.f_panel_bg_items:
            self.canvas.itemconfig(item, state="normal")
        if key == "step5":
            for item in self.f5_items:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p1":
            for item in self.f6_groups[0]:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p2":
            for item in self.f6_groups[1]:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step6_p3":
            for item in self.f6_groups[2]:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step7":
            for item in self.f7_header:
                self.canvas.itemconfig(item, state="normal")
            for item in self.f7_row_items:
                self.canvas.itemconfig(item, state="normal")
        elif key == "step8":
            for item in self.f8_items:
                self.canvas.itemconfig(item, state="normal")

    def calc_values(self, r2):
        r_total = 100.0 + r2
        i = 12.0 / r_total if r_total > 0 else 12.0 / 100.0
        return i, i*100.0, i*r2

    def update_readings(self, r2):
        i, u1, u2 = self.calc_values(r2)
        i_ma = i * 1000
        self.canvas.itemconfig(self.pa1_val, text="%d мА" % i_ma)
        self.canvas.itemconfig(self.pv1_val, text="%.1f В" % u1)
        self.canvas.itemconfig(self.pv2_val, text="%.1f В" % u2)
        self.canvas.itemconfig(self.pv3_val, text="%.1f В" % (u1+u2))
        if hasattr(self, "r2_label"):
            self.canvas.itemconfig(self.r2_label, text="R2 = %d \u03a9" % r2)

    PHASES = [
        ("step0",       "Шаг 1 из 9","Приветствие"),
        ("step1",       "Шаг 2 из 9","Появление резисторов R1 = 100 Ом и R2 = 0\u2026200 Ом"),
        ("step2",       "Шаг 3 из 9","Добавление измерительных приборов PA1, PV1\u2013PV3"),
        ("step3",       "Шаг 4 из 9","Подключение источника E1 = 12 В"),
        ("step4",       "Шаг 5 из 9","Сборка цепи: последовательное соединение"),
        ("step5",       "Шаг 6 из 9","Показания приборов при R2 = 200 Ом"),
        ("step6_p1",    "Шаг 7 из 9","Свойство 1: U = U\u2081 + U\u2082 (12 = 4 + 8)"),
        ("step6_p2",    "Шаг 7 из 9","Свойство 2: R\u2082/R\u2081 = U\u2082/U\u2081 = 2"),
        ("step6_p3",    "Шаг 7 из 9","Свойство 3: Rэкв = R\u2081 + R\u2082 = 300 Ом"),
        ("step7_r2_150","Шаг 8 из 9","R\u2082 = 150 Ом \u2013 показания меняются"),
        ("step7_r2_100","Шаг 8 из 9","R\u2082 = 100 Ом \u2013 ток растёт"),
        ("step7_r2_50", "Шаг 8 из 9","R\u2082 = 50 Ом \u2013 напряжение U\u2082 падает"),
        ("step7_r2_25", "Шаг 8 из 9","R\u2082 = 25 Ом \u2013 почти короткое замыкание"),
        ("step7_r2_0",  "Шаг 8 из 9","R\u2082 = 0 Ом \u2013 всё напряжение на R\u2081!"),
        ("step8",       "Шаг 9 из 9","Итог: свойства последовательного соединения"),
    ]
    PHASE_DURATIONS = [TIMINGS[k] for k in (
        "step0_welcome",
        "step1_show_resistors","step2_show_meters","step3_show_battery",
        "step4_build_wires","step5_initial_values",
        "step6_property1","step6_property2","step6_property3",
        "step7_r2_150","step7_r2_100","step7_r2_50","step7_r2_25","step7_r2_0",
        "step8_finish",
    )]
    PHASE_FORMULA = [
        None,
        None,"step5",None,None,"step5",
        "step6_p1","step6_p2","step6_p3",
        "step7","step7","step7","step7","step7",
        "step8",
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

        if idx < len(NARRATION):
            if self._speech_delay_id:
                self.root.after_cancel(self._speech_delay_id)
            # Show speech text immediately so it syncs with voice
            self.show_speech(NARRATION[idx])
            self._speech_delay_id = None
            self._speech_ended = False
            self._speech_phase_idx = idx
            self._min_phase_dur_ms = dur
            cb_idx = idx
            self.tts.speak(NARRATION[idx], callback=lambda: self.root.after_idle(lambda: self._on_speech_ended(cb_idx)))
        else:
            self._speech_ended = True
            self.show_speech(status)

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

        # Schedule current phase sub-groups with trigger-based delays
        if key in SUB_PHASE_GROUPS:
            groups = SUB_PHASE_GROUPS[key]
            if key not in self.active_sub_groups:
                self.active_sub_groups[key] = set()
            for sub_idx, sg in enumerate(groups):
                delay = self._get_trigger_delay(key, sg["trigger"])
                if delay <= 50:
                    self.active_sub_groups[key].add(sub_idx)
                else:
                    deadline = time.time() + delay / 1000.0
                    tid = self.root.after(delay, lambda k=key, si=sub_idx: self._activate_sub_group(k, si))
                    self._sub_phase_timers.append((tid, deadline, key, sub_idx))
        else:
            self.active_phases.add(key)

        # If step5: pre-set all reading texts (hidden via _val tag separation)
        if idx == 5:
            self.update_readings(200)

        self.refresh_display()

        # Formula
        fkey = self.PHASE_FORMULA[idx]
        if fkey:
            self.show_formula(fkey)
        else:
            for item in self.formula_items:
                self.canvas.itemconfig(item, state="hidden")
            for item in self.f_panel_bg_items:
                self.canvas.itemconfig(item, state="normal")

        if idx == 0:
            pass  # welcome greeting, no circuit elements yet
        elif idx == 1:
            pass  # readings already hidden, shown via sub-phases
        elif idx == 5:
            pass  # readings already hidden, shown via sub-phases
        elif idx == 6:
            self.highlight_property1()
            self._highlight_formula_data("step6_p1", 0)
        elif idx == 7:
            self.highlight_property2()
            self._highlight_formula_data("step6_p2", 0)
        elif idx == 8:
            self.highlight_property3()
            self._highlight_formula_data("step6_p3", 0)
        elif 9 <= idx <= 13:
            r2_vals = [200,150,100,50,25,0]
            sub = idx - 9
            if sub < len(r2_vals):
                self.update_readings(r2_vals[sub])
                self.highlight_r2_table_row(sub)
                self.highlight_junction_points(True)
        elif idx == 14:
            pass

        if idx not in (6,7,8):
            self.clear_highlights()

        if idx == 4:
            self.wire_substep = 0
            self.wire_in_progress = True
            self.wires_visible = 0
            self.refresh_display()
            self.root.after(50, self.advance_wires)
        else:
            self.wire_in_progress = False

        self.phase_start = time.time()
        if self._speech_ended:
            self.phase_remaining = dur + 500
            self.schedule_next(self.phase_remaining)
        else:
            # Backup timer (30s safety net); actual transition driven by _on_speech_ended
            self.phase_remaining = dur + 30000
            self.schedule_next(self.phase_remaining)

    def _on_speech_ended(self, phase_idx):
        """Called (in main thread) when TTS finishes speaking the current narration."""
        if phase_idx != self._speech_phase_idx:
            return  # stale callback from a previous phase
        if self._in_transition or self.stopped or self.paused:
            return
        self._speech_ended = True
        # Cancel backup timer if still pending
        if self.phase_timer:
            self.root.after_cancel(self.phase_timer)
            self.phase_timer = None
        elapsed = (time.time() - self.phase_start) * 1000
        if elapsed >= self._min_phase_dur_ms:
            self.root.after_idle(self.on_timeout)
        else:
            remaining = int(self._min_phase_dur_ms - elapsed + 300)
            self.schedule_next(remaining)

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
                # Slightly speed up toward the end for a more natural feel
                remaining = len(self.wire_items) - self.wire_substep
                delay = 200 if remaining > 6 else 160
                self.wire_timer = self.root.after(delay, self.advance_wires)
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
            self._hl_frame(cx-45, cy-45, cx+45, cy+45, "#E65100")
        self._hl_text("U = U\u2081 + U\u2082 = 4 + 8 = 12 В", "#D32F2F")

    def highlight_property2(self):
        self.clear_highlights()
        self._hl_frame(R1_LEFT-10, R1_Y-32, R1_RIGHT+10, R1_Y+32, "#1565C0")
        self._hl_frame(R2_LEFT-10, R2_Y-32, R2_RIGHT+10, R2_Y+32, "#1565C0")
        self._hl_frame(PV1_CENTER[0]-45, PV1_CENTER[1]-45, PV1_CENTER[0]+45, PV1_CENTER[1]+45, "#2E7D32")
        self._hl_frame(PV2_CENTER[0]-45, PV2_CENTER[1]-45, PV2_CENTER[0]+45, PV2_CENTER[1]+45, "#2E7D32")
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
        for jx, jy in JUNCTION_DOTS:
            dot = self.canvas.create_oval(
                jx-8, jy-8, jx+8, jy+8,
                fill="#212121", outline="", tags="hl_junc"
            )
            self._junction_hl_items.append(dot)
        self.canvas.tag_raise("speech")

    def _clear_formula_highlights(self):
        for item in self.canvas.find_withtag("f_hl"):
            self.canvas.delete(item)

    def _highlight_formula_data(self, phase_key, sub_idx):
        self._clear_formula_highlights()
        s = self._scale
        if phase_key == "step5":
            # f5_items: [header(0), R1(1), R2(2), I(3), U1(4), U2(5), Uобщ(6)]
            row_map = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6}
            if sub_idx in row_map:
                ri = row_map[sub_idx]
                if ri < len(self.f5_items):
                    bbox = self.canvas.bbox(self.f5_items[ri])
                    if bbox:
                        x1, y1, x2, y2 = bbox
                        pad = round(4 * s)
                        self.canvas.create_rectangle(
                            x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                            fill="#FFF9C4", outline="", tags="f_hl"
                        )
                        self.canvas.tag_lower("f_hl")
        elif phase_key in ("step6_p1", "step6_p2", "step6_p3"):
            # Highlight the formula & value lines (indices 0,1) of the current group
            grp_idx = {"step6_p1": 0, "step6_p2": 1, "step6_p3": 2}.get(phase_key, 0)
            if grp_idx < len(self.f6_groups):
                for li in (0, 1):
                    if li < len(self.f6_groups[grp_idx]):
                        bbox = self.canvas.bbox(self.f6_groups[grp_idx][li])
                        if bbox:
                            x1, y1, x2, y2 = bbox
                            pad = round(4 * s)
                            self.canvas.create_rectangle(
                                x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                                fill="#E3F2FD", outline="", tags="f_hl"
                            )
                            self.canvas.tag_lower("f_hl")

    def highlight_r2_table_row(self, row_idx):
        cols = 5
        for i, item in enumerate(self.f7_row_items):
            ri = i // cols
            fc = "#D32F2F" if ri == row_idx else C_TEXT
            fw = "bold" if ri == row_idx else "normal"
            self.canvas.itemconfig(item, fill=fc, font=("Arial", self._sf(23), fw))
        # Also add a background highlight bar to the right of the table
        self._clear_formula_highlights()
        s = self._scale
        for i, item in enumerate(self.f7_row_items):
            ri = i // cols
            if ri == row_idx:
                bbox = self.canvas.bbox(item)
                if bbox:
                    x1, y1, x2, y2 = bbox
                    pad = round(5 * s)
                    self.canvas.create_rectangle(
                        x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                        fill="#E8F5E9", outline="", tags="f_hl"
                    )
                    self.canvas.tag_lower("f_hl")

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
            self.tts.pause()
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
            self.tts.resume()
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

    def on_reset(self):
        self.stopped = True
        self.paused = False
        self.tts.stop()
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
                self.tts.stop()
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
        self.status_label.config(
            text="Видеоурок завершён! Нажмите «СБРОС» для повтора."
        )
        self.timer_label.config(text="\u2714")
        self.step_label.config(text="Шаг 9 из 9")
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
