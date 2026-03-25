"""
Simulador de Regeneración DPF - Coca-Cola FEMSA
Para Raspberry Pi 4 con pantalla táctil IPS DSI 7" (800x480)
EURO VI - Filtro de Partículas Diésel
"""

import tkinter as tk
import threading
import subprocess
import os
import sys
import math

# ─────────────────────────────────────────────
# Paleta de colores (tema tablero vehicular)
# ─────────────────────────────────────────────
COLOR_BG        = "#0a0a0f"     # Negro profundo (fondo principal)
COLOR_PANEL     = "#12121a"     # Panel oscuro
COLOR_BORDER    = "#1e1e2e"     # Borde sutil
COLOR_WHITE     = "#f0f0f0"
COLOR_GRAY      = "#8888aa"
COLOR_AMBER     = "#ffb300"     # Amarillo/Ámbar vehículo
COLOR_AMBER_DIM = "#554400"     # Ámbar apagado
COLOR_RED       = "#e53935"     # Rojo alerta
COLOR_RED_DIM   = "#440000"     # Rojo apagado
COLOR_GREEN     = "#43a047"     # Verde ok
COLOR_GREEN_DIM = "#0d2b0e"     # Verde apagado
COLOR_COCA_RED  = "#e2000f"     # Rojo Coca-Cola
COLOR_COCA_DARK = "#8b0000"     # Rojo oscuro Coca-Cola
COLOR_BLUE      = "#1565c0"
COLOR_BLUE_LIGHT= "#42a5f5"

FONT_TITLE   = ("Helvetica", 20, "bold")
FONT_LABEL   = ("Helvetica", 14, "bold")
FONT_SMALL   = ("Helvetica", 11)
FONT_TINY    = ("Helvetica", 9)
FONT_BIG     = ("Helvetica", 28, "bold")
FONT_HUGE    = ("Helvetica", 36, "bold")
FONT_MONO    = ("Courier", 13, "bold")

SCREEN_W = 800
SCREEN_H = 480


# ─────────────────────────────────────────────
# Función de sonido (cross-platform)
# ─────────────────────────────────────────────
def beep_short(count=1):
    """Emite pitido(s) corto(s) en segundo plano."""
    def _play():
        for _ in range(count):
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.Beep(880, 200)
                else:
                    # Raspberry Pi / Linux: usa el bell del terminal
                    subprocess.Popen(
                        ["bash", "-c", "echo -ne '\\a'"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            except Exception:
                pass
    threading.Thread(target=_play, daemon=True).start()


def beep_continuous_start():
    """Retorna un evento de parada para el pitido continuo."""
    stop_event = threading.Event()

    def _loop():
        while not stop_event.is_set():
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.Beep(660, 400)
                else:
                    subprocess.Popen(
                        ["bash", "-c", "echo -ne '\\a'"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    ).wait()
                stop_event.wait(0.6)
            except Exception:
                stop_event.wait(0.6)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return stop_event


# ─────────────────────────────────────────────
# Helpers de dibujo en Canvas
# ─────────────────────────────────────────────
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=15, **kwargs):
    """Dibuja un rectángulo con esquinas redondeadas en canvas."""
    canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  style="pieslice", **kwargs)
    canvas.create_rectangle(x1+r, y1,   x2-r, y2,     **kwargs)
    canvas.create_rectangle(x1,   y1+r, x2,   y2-r,   **kwargs)


def draw_logo_cocacola_femsa(canvas, cx, cy, scale=1.0):
    """Dibuja el logo estilizado de Coca-Cola FEMSA en canvas."""
    w = int(220 * scale)
    h = int(70 * scale)
    r = int(12 * scale)

    # Fondo rojo con esquinas redondeadas
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = cx + w // 2, cy + h // 2
    draw_rounded_rect(canvas, x1, y1, x2, y2, r=r,
                      fill=COLOR_COCA_RED, outline=COLOR_COCA_DARK, width=2)

    # Banda blanca horizontal decorativa
    band_y1 = cy - int(5 * scale)
    band_y2 = cy + int(5 * scale)
    canvas.create_rectangle(x1+r, band_y1, x2-r, band_y2,
                             fill="white", outline="")

    # Texto "Coca-Cola" arriba
    canvas.create_text(cx, cy - int(18 * scale),
                       text="Coca-Cola", fill="white",
                       font=("Helvetica", int(16 * scale), "bold italic"))

    # Texto "FEMSA" abajo
    canvas.create_text(cx, cy + int(18 * scale),
                       text="F E M S A", fill="white",
                       font=("Helvetica", int(11 * scale), "bold"))


def draw_dpf_icon(canvas, cx, cy, color="#888", size=28):
    """Dibuja el ícono de filtro DPF (panal de tubos)."""
    tube_w = size // 5
    gap = 3
    total_w = 5 * tube_w + 4 * gap
    x0 = cx - total_w // 2
    for i in range(5):
        tx = x0 + i * (tube_w + gap)
        canvas.create_rectangle(tx, cy - size // 2,
                                 tx + tube_w, cy + size // 2,
                                 fill=color, outline=COLOR_BG, width=1)
    # Marco
    canvas.create_rectangle(cx - total_w // 2 - 3, cy - size // 2 - 3,
                             cx + total_w // 2 + 3, cy + size // 2 + 3,
                             fill="", outline=color, width=2)


def draw_warning_triangle(canvas, cx, cy, color=COLOR_AMBER, size=30):
    """Dibuja triángulo de advertencia con signo de exclamación."""
    h = int(size * 0.866)
    pts = [cx, cy - h * 2 // 3,
           cx - size, cy + h // 3,
           cx + size, cy + h // 3]
    canvas.create_polygon(pts, fill=color, outline="black", width=2)
    canvas.create_text(cx, cy + int(h * 0.05),
                       text="!", fill="black",
                       font=("Helvetica", int(size * 0.9), "bold"))


def draw_stop_light(canvas, cx, cy, color=COLOR_RED, size=34):
    """Dibuja octágono de señal STOP."""
    pts = []
    for i in range(8):
        angle = math.radians(i * 45 + 22.5)
        pts.extend([cx + size * math.cos(angle),
                    cy + size * math.sin(angle)])
    canvas.create_polygon(pts, fill=color, outline="darkred", width=3)
    canvas.create_text(cx, cy, text="STOP",
                       fill="white", font=("Helvetica", int(size * 0.5), "bold"))


def draw_gauge(canvas, cx, cy, radius, value, max_value,
               label="", unit="", color=COLOR_GREEN):
    """
    Dibuja un velocímetro/medidor semicircular.
    value: valor actual  max_value: máximo
    """
    # Arco de fondo
    canvas.create_arc(cx - radius, cy - radius,
                      cx + radius, cy + radius,
                      start=220, extent=-260,
                      style="arc", outline=COLOR_BORDER, width=8)

    # Arco de valor
    angle = int(260 * (value / max_value))
    canvas.create_arc(cx - radius, cy - radius,
                      cx + radius, cy + radius,
                      start=220, extent=-angle,
                      style="arc", outline=color, width=8)

    # Aguja
    needle_angle = math.radians(220 - angle)
    nx = cx + int((radius - 12) * math.cos(needle_angle))
    ny = cy - int((radius - 12) * math.sin(needle_angle))
    canvas.create_line(cx, cy, nx, ny, fill="white", width=3)
    canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="white")

    # Texto valor
    canvas.create_text(cx, cy + radius // 3,
                       text=f"{int(value)}", fill="white",
                       font=("Helvetica", int(radius * 0.45), "bold"))
    canvas.create_text(cx, cy + radius // 3 + int(radius * 0.3),
                       text=unit, fill=COLOR_GRAY,
                       font=("Helvetica", int(radius * 0.2)))
    if label:
        canvas.create_text(cx, cy - radius - 10,
                           text=label, fill=COLOR_GRAY,
                           font=("Helvetica", 10))


def draw_saturation_bar(canvas, x, y, width, height, pct, color=COLOR_GREEN):
    """Barra horizontal de saturación del DPF."""
    # Fondo
    canvas.create_rectangle(x, y, x + width, y + height,
                             fill=COLOR_BORDER, outline=COLOR_GRAY, width=1)
    # Relleno
    fill_w = int(width * min(pct / 100, 1.0))
    if fill_w > 0:
        canvas.create_rectangle(x + 1, y + 1,
                                 x + fill_w, y + height - 1,
                                 fill=color, outline="")
    # Marcas de nivel
    for mark_pct, mark_label in [(35, "35%"), (70, "70%"), (90, "90%"), (100, "100%")]:
        mx = x + int(width * mark_pct / 100)
        canvas.create_line(mx, y, mx, y + height, fill="#555", width=1, dash=(3, 3))
        canvas.create_text(mx, y - 8, text=mark_label,
                           fill=COLOR_GRAY, font=("Helvetica", 7))

    # Porcentaje
    canvas.create_text(x + width // 2, y + height // 2,
                       text=f"{pct:.0f}%", fill="white",
                       font=("Helvetica", int(height * 0.55), "bold"))


def draw_warning_light(canvas, cx, cy, color, label="", on=True, radius=20):
    """Dibuja una luz de advertencia circular."""
    fill_color = color if on else COLOR_BORDER
    glow = "" if not on else color

    # Halo exterior si está encendida
    if on:
        canvas.create_oval(cx - radius - 4, cy - radius - 4,
                           cx + radius + 4, cy + radius + 4,
                           fill="", outline=color, width=2)
    canvas.create_oval(cx - radius, cy - radius,
                       cx + radius, cy + radius,
                       fill=fill_color, outline="#333", width=2)
    if label:
        canvas.create_text(cx, cy + radius + 12,
                           text=label, fill=COLOR_GRAY if not on else color,
                           font=("Helvetica", 8))


def make_button(parent, text, command, bg=COLOR_BLUE, fg="white",
                width=18, height=2, font=FONT_LABEL):
    """Crea un botón estilizado para pantalla táctil."""
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=COLOR_BLUE_LIGHT,
        activeforeground="white",
        font=font, width=width, height=height,
        relief="flat", bd=0, cursor="hand2",
        highlightthickness=2, highlightbackground=COLOR_BORDER
    )
    return btn


# ═══════════════════════════════════════════════════
# Clase principal del simulador
# ═══════════════════════════════════════════════════
class SimuladorDPF(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador DPF - Coca-Cola FEMSA")
        self.geometry(f"{SCREEN_W}x{SCREEN_H}")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)

        # Modo kiosco: cambiar a True para pantalla táctil dedicada en Raspberry Pi.
        # Mantener en False durante desarrollo y pruebas en escritorio.
        _FULLSCREEN = False
        try:
            self.attributes("-fullscreen", _FULLSCREEN)
        except Exception:
            pass

        # Estado interno
        self._blink_after = None        # ID del after() para parpadeo
        self._blink_state = False       # Estado del parpadeo
        self._beep_stop_event = None    # Evento para detener pitido continuo
        self._current_screen = None

        self.mostrar_inicio()

    # ─────────────────────────────────────────
    # Utilidades de navegación
    # ─────────────────────────────────────────
    def _clear(self):
        """Limpia la ventana y detiene animaciones."""
        if self._blink_after is not None:
            self.after_cancel(self._blink_after)
            self._blink_after = None
        if self._beep_stop_event is not None:
            self._beep_stop_event.set()
            self._beep_stop_event = None
        for w in self.winfo_children():
            w.destroy()

    def _header(self, canvas, subtitle=""):
        """Dibuja cabecera común con logo y subtítulo."""
        # Franja superior
        canvas.create_rectangle(0, 0, SCREEN_W, 60,
                                 fill=COLOR_PANEL, outline="")
        canvas.create_line(0, 60, SCREEN_W, 60, fill=COLOR_BORDER, width=2)

        # Logo Coca-Cola FEMSA
        draw_logo_cocacola_femsa(canvas, 110, 30, scale=0.75)

        # Título del simulador
        canvas.create_text(SCREEN_W // 2 + 30, 20,
                           text="Simulador de Regeneración DPF",
                           fill=COLOR_WHITE, font=("Helvetica", 13, "bold"))
        if subtitle:
            canvas.create_text(SCREEN_W // 2 + 30, 42,
                               text=subtitle,
                               fill=COLOR_GRAY, font=("Helvetica", 10))

        # Línea decorativa derecha - ícono DPF
        draw_dpf_icon(canvas, SCREEN_W - 35, 30, color=COLOR_GRAY, size=22)

    def _footer(self, canvas, text=""):
        """Dibuja pie de página."""
        canvas.create_rectangle(0, SCREEN_H - 28, SCREEN_W, SCREEN_H,
                                 fill=COLOR_PANEL, outline="")
        canvas.create_line(0, SCREEN_H - 28, SCREEN_W, SCREEN_H - 28,
                           fill=COLOR_BORDER, width=1)
        canvas.create_text(SCREEN_W // 2, SCREEN_H - 13,
                           text=text, fill=COLOR_GRAY,
                           font=("Helvetica", 8))

    # ─────────────────────────────────────────
    # PANTALLA 0: Inicio / Splash
    # ─────────────────────────────────────────
    def mostrar_inicio(self):
        self._clear()
        self._current_screen = "inicio"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Fondo decorativo - líneas de cuadrícula suaves
        for x in range(0, SCREEN_W, 40):
            canvas.create_line(x, 0, x, SCREEN_H, fill="#0f0f18", width=1)
        for y in range(0, SCREEN_H, 40):
            canvas.create_line(0, y, SCREEN_W, y, fill="#0f0f18", width=1)

        # Logo grande centrado arriba
        draw_logo_cocacola_femsa(canvas, SCREEN_W // 2, 110, scale=1.4)

        # Ícono DPF grande
        draw_dpf_icon(canvas, SCREEN_W // 2, 205, color=COLOR_GRAY, size=34)

        # Título principal
        canvas.create_text(SCREEN_W // 2, 255,
                           text="SIMULADOR DPF",
                           fill=COLOR_WHITE, font=("Helvetica", 26, "bold"))
        canvas.create_text(SCREEN_W // 2, 283,
                           text="Regeneración del Filtro de Partículas Diésel · EURO VI",
                           fill=COLOR_GRAY, font=("Helvetica", 11))

        # Línea decorativa
        canvas.create_line(SCREEN_W // 2 - 160, 300, SCREEN_W // 2 + 160, 300,
                           fill=COLOR_BORDER, width=2)

        # Botón táctil grande
        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2, 370, window=btn_frame)

        btn = make_button(btn_frame, "▶  INICIAR SIMULACIÓN",
                          self.mostrar_operacion_normal,
                          bg=COLOR_GREEN, width=24, height=2,
                          font=("Helvetica", 16, "bold"))
        btn.pack(padx=4, pady=4)

        # Versión / info
        canvas.create_text(SCREEN_W // 2, 445,
                           text="Raspberry Pi 4 · Pantalla IPS 7\" 800×480 · Python / Tkinter",
                           fill="#333355", font=("Helvetica", 8))

    # ─────────────────────────────────────────
    # PANTALLA 1: Operación Normal (0-30%)
    # ─────────────────────────────────────────
    def mostrar_operacion_normal(self):
        self._clear()
        self._current_screen = "normal"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="Estado: Operación Normal")

        # Gauges principales
        draw_gauge(canvas, 120, 250, 80, 65, 120,
                   label="VELOCIDAD", unit="km/h", color=COLOR_GREEN)
        draw_gauge(canvas, 310, 250, 80, 1600, 3000,
                   label="RPM", unit="rpm", color=COLOR_BLUE_LIGHT)

        # Barra de saturación DPF
        canvas.create_text(SCREEN_W // 2 + 95, 80,
                           text="SATURACIÓN DPF",
                           fill=COLOR_GRAY, font=("Helvetica", 10, "bold"))
        draw_saturation_bar(canvas, 440, 95, 320, 28, 18, color=COLOR_GREEN)

        # Temperatura motor (indicador)
        canvas.create_text(470, 145, text="TEMP. MOTOR",
                           fill=COLOR_GRAY, font=("Helvetica", 9))
        canvas.create_rectangle(440, 157, 760, 172,
                                 fill=COLOR_BORDER, outline=COLOR_GRAY, width=1)
        canvas.create_rectangle(441, 158, 581, 171,
                                 fill=COLOR_GREEN, outline="")
        canvas.create_text(600, 164, text="82 °C  ✓",
                           fill=COLOR_GREEN, font=("Helvetica", 9, "bold"))

        # Luces de estado (todas APAGADAS - operación normal)
        lx = 460
        for i, (lbl, col) in enumerate([
            ("DPF", COLOR_AMBER),
            ("MOTOR", COLOR_AMBER),
            ("STOP", COLOR_RED),
        ]):
            draw_warning_light(canvas, lx + i * 70, 220, col,
                               label=lbl, on=False, radius=18)

        # Icono check verde
        canvas.create_text(600, 290,
                           text="✔", fill=COLOR_GREEN,
                           font=("Helvetica", 40, "bold"))
        canvas.create_text(600, 335,
                           text="Sistema OK", fill=COLOR_GREEN,
                           font=("Helvetica", 13, "bold"))

        # Mensajes de estado
        msgs = [
            "● DPF operando con normalidad (0 – 30% saturación)",
            "● Sin alertas activas en el sistema",
            "● Regeneración pasiva en curso automáticamente",
        ]
        for i, m in enumerate(msgs):
            canvas.create_text(460, 370 + i * 20, text=m,
                               fill=COLOR_WHITE, font=("Helvetica", 10),
                               anchor="w")

        self._footer(canvas, "Operación normal · El sistema de regeneración funciona correctamente")

        # Botones de navegación
        nav = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2 - 60, 445, window=nav)
        make_button(nav, "← Inicio", self.mostrar_inicio,
                    bg="#222233", width=12, height=1,
                    font=FONT_SMALL).pack(side="left", padx=5)
        make_button(nav, "Simular Nivel 1 →", self.mostrar_nivel1,
                    bg=COLOR_AMBER, fg="black", width=18, height=1,
                    font=("Helvetica", 11, "bold")).pack(side="left", padx=5)

    # ─────────────────────────────────────────
    # PANTALLA 2: NIVEL 1 (35-50%)
    # ─────────────────────────────────────────
    def mostrar_nivel1(self):
        self._clear()
        self._current_screen = "nivel1"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="NIVEL 1 · Regeneración Manual / Pasiva")

        # Barra saturación
        canvas.create_text(SCREEN_W // 2 + 95, 80,
                           text="SATURACIÓN DPF",
                           fill=COLOR_AMBER, font=("Helvetica", 10, "bold"))
        draw_saturation_bar(canvas, 440, 95, 320, 28, 43, color=COLOR_AMBER)

        # Luz amarilla FIJA
        canvas.create_text(200, 85, text="LUZ ALERTA",
                           fill=COLOR_GRAY, font=("Helvetica", 9))
        draw_warning_light(canvas, 200, 130, COLOR_AMBER,
                           label="DPF", on=True, radius=28)
        draw_warning_triangle(canvas, 200, 210, color=COLOR_AMBER, size=22)

        # Gauges
        draw_gauge(canvas, 120, 310, 70, 50, 120,
                   label="VELOCIDAD", unit="km/h", color=COLOR_AMBER)
        draw_gauge(canvas, 310, 310, 70, 1400, 3000,
                   label="RPM", unit="rpm", color=COLOR_AMBER)

        # Mensajes
        msgs = [
            "⚠  DPF entre 35% – 50% de saturación",
            "   Realice regeneración pasiva o manual",
            "   • Pasiva: conduzca ≥ 60 km/h en autopista",
            "   • Manual: presione el botón de regeneración",
        ]
        for i, m in enumerate(msgs):
            color = COLOR_AMBER if i == 0 else COLOR_WHITE
            canvas.create_text(480, 130 + i * 22, text=m,
                               fill=color,
                               font=("Helvetica", 10 if i == 0 else 9),
                               anchor="w")

        self._footer(canvas, "Nivel 1 · 35–50% Saturación · Luz amarilla FIJA")

        # Botones de acción
        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2 + 60, 380, window=btn_frame)

        make_button(btn_frame,
                    "🚗  Regeneración Pasiva\n(Conducir ≥ 60 km/h)",
                    self._regen_pasiva_nivel1,
                    bg="#1a4a1a", fg=COLOR_GREEN,
                    width=26, height=2,
                    font=("Helvetica", 10, "bold")).pack(pady=4)

        make_button(btn_frame,
                    "🔧  Regeneración Manual\n(Presionar botón)",
                    self._regen_manual_nivel1,
                    bg="#4a3a00", fg=COLOR_AMBER,
                    width=26, height=2,
                    font=("Helvetica", 10, "bold")).pack(pady=4)

        # Nav
        nav = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(100, 445, window=nav)
        make_button(nav, "← Atrás", self.mostrar_operacion_normal,
                    bg="#222233", width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)
        make_button(nav, "Nivel 2 →", self.mostrar_nivel2,
                    bg="#554400", fg=COLOR_AMBER, width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)

    def _regen_pasiva_nivel1(self):
        self._mostrar_regenerando(
            titulo="Regeneración Pasiva en Curso",
            mensaje="El vehículo circula a ≥ 60 km/h.\nLa temperatura de escape eleva la combustión\nde las partículas atrapadas en el DPF.",
            duracion_seg=4,
            callback=self._regen_exitosa,
        )

    def _regen_manual_nivel1(self):
        self._mostrar_regenerando(
            titulo="Regeneración Manual Iniciada",
            mensaje="Botón de regeneración manual activado.\nMantener el motor a 1500 rpm.\nTiempo estimado: ~20 minutos.",
            duracion_seg=4,
            callback=self._regen_exitosa,
        )

    # ─────────────────────────────────────────
    # PANTALLA 3: NIVEL 2 (70-90%)
    # ─────────────────────────────────────────
    def mostrar_nivel2(self):
        self._clear()
        self._current_screen = "nivel2"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="NIVEL 2 · Regeneración Manual Obligatoria")

        draw_saturation_bar(canvas, 440, 95, 320, 28, 80, color=COLOR_AMBER)
        canvas.create_text(SCREEN_W // 2 + 95, 80,
                           text="SATURACIÓN DPF",
                           fill=COLOR_AMBER, font=("Helvetica", 10, "bold"))

        # Luz ámbar (para animación)
        self._amber_light_id = None
        self._amber_label_id = None
        canvas.create_text(200, 85, text="LUZ ALERTA",
                           fill=COLOR_GRAY, font=("Helvetica", 9))
        self._amber_canvas_n2 = canvas
        self._amber_cx, self._amber_cy = 200, 140
        self._amber_radius = 28
        self._amber_on_n2 = True
        self._draw_amber_n2()
        draw_warning_triangle(canvas, 200, 225, color=COLOR_AMBER, size=22)

        draw_gauge(canvas, 120, 320, 65, 35, 120,
                   label="VELOCIDAD", unit="km/h", color=COLOR_AMBER)
        draw_gauge(canvas, 310, 320, 65, 1200, 3000,
                   label="RPM", unit="rpm", color=COLOR_AMBER)

        msgs = [
            "⚠⚠  DPF entre 70% – 90% de saturación",
            "   REGENERACIÓN MANUAL OBLIGATORIA",
            "   • El motor puede experimentar pérdida de potencia",
            "   • Estacione el vehículo en zona segura y ventilada",
            "   • Active la regeneración manual y espere ~20 min",
        ]
        for i, m in enumerate(msgs):
            color = COLOR_AMBER if i <= 1 else COLOR_WHITE
            fnt = ("Helvetica", 10, "bold") if i <= 1 else ("Helvetica", 9)
            canvas.create_text(480, 120 + i * 23, text=m,
                               fill=color, font=fnt, anchor="w")

        self._footer(canvas, "Nivel 2 · 70–90% Saturación · Luz amarilla INTERMITENTE")

        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2 + 60, 380, window=btn_frame)
        make_button(btn_frame,
                    "🔧  Iniciar Regeneración Manual Obligatoria",
                    self._regen_manual_nivel2,
                    bg=COLOR_AMBER, fg="black",
                    width=36, height=2,
                    font=("Helvetica", 11, "bold")).pack(pady=4)

        nav = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(100, 445, window=nav)
        make_button(nav, "← Nivel 1", self.mostrar_nivel1,
                    bg="#222233", width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)
        make_button(nav, "Nivel 3 →", self.mostrar_nivel3,
                    bg="#553300", fg=COLOR_AMBER, width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)

        self._blink_amber_n2()

    def _draw_amber_n2(self):
        c = self._amber_canvas_n2
        cx, cy, r = self._amber_cx, self._amber_cy, self._amber_radius
        on = self._amber_on_n2
        fill_c = COLOR_AMBER if on else COLOR_AMBER_DIM
        # Borrar y redibujar
        c.delete("amber_light_n2")
        if on:
            c.create_oval(cx-r-5, cy-r-5, cx+r+5, cy+r+5,
                          fill="", outline=COLOR_AMBER, width=2,
                          tags="amber_light_n2")
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      fill=fill_c, outline="#333", width=2,
                      tags="amber_light_n2")
        c.create_text(cx, cy+r+12, text="DPF",
                      fill=COLOR_AMBER if on else COLOR_GRAY,
                      font=("Helvetica", 8), tags="amber_light_n2")

    def _blink_amber_n2(self):
        if self._current_screen != "nivel2":
            return
        self._amber_on_n2 = not self._amber_on_n2
        self._draw_amber_n2()
        self._blink_after = self.after(600, self._blink_amber_n2)

    def _regen_manual_nivel2(self):
        self._mostrar_regenerando(
            titulo="Regeneración Manual — Nivel 2",
            mensaje="Motor en ralentí. Temperatura del DPF subiendo.\n"
                    "No apague el motor durante el proceso.\n"
                    "Tiempo estimado: ~20 minutos.",
            duracion_seg=4,
            callback=self._regen_exitosa,
        )

    # ─────────────────────────────────────────
    # PANTALLA 4: NIVEL 3 (90-100%)
    # ─────────────────────────────────────────
    def mostrar_nivel3(self):
        self._clear()
        self._current_screen = "nivel3"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="NIVEL 3 · Alerta Crítica — Regeneración de Emergencia")

        draw_saturation_bar(canvas, 440, 95, 320, 28, 95, color=COLOR_RED)
        canvas.create_text(SCREEN_W // 2 + 95, 80,
                           text="SATURACIÓN DPF",
                           fill=COLOR_RED, font=("Helvetica", 10, "bold"))

        # Luz amarilla intermitente nivel 3
        self._amber_canvas_n3 = canvas
        self._amber_cx3, self._amber_cy3, self._amber_r3 = 200, 140, 28
        self._amber_on_n3 = True
        self._draw_amber_n3()
        draw_warning_triangle(canvas, 200, 225, color=COLOR_RED, size=24)

        # Torque reducido
        canvas.create_text(310, 100, text="TORQUE",
                           fill=COLOR_RED, font=("Helvetica", 9, "bold"))
        draw_gauge(canvas, 310, 200, 65, 60, 100,
                   label="TORQUE (%)", unit="%", color=COLOR_RED)
        canvas.create_text(310, 280, text="↓ 40% reducido",
                           fill=COLOR_RED, font=("Helvetica", 9, "bold"))

        draw_gauge(canvas, 120, 330, 60, 25, 120,
                   label="VELOCIDAD", unit="km/h", color=COLOR_RED)

        msgs = [
            "🚨  DPF entre 90% – 100% de saturación",
            "   REGENERACIÓN DE EMERGENCIA REQUERIDA",
            "   ▶  Torque del motor reducido en un 40%",
            "   ▶  Estacione inmediatamente en zona ventilada",
            "   ▶  Active regeneración de emergencia",
            "   ▶  No opere el vehículo hasta completar proceso",
        ]
        for i, m in enumerate(msgs):
            color = COLOR_RED if i <= 1 else COLOR_WHITE
            fnt = ("Helvetica", 10, "bold") if i <= 1 else ("Helvetica", 9)
            canvas.create_text(490, 110 + i * 22, text=m,
                               fill=color, font=fnt, anchor="w")

        self._footer(canvas,
                     "Nivel 3 · 90–100% Saturación · Luz amarilla INTERMITENTE + pitidos")

        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2 + 60, 380, window=btn_frame)
        make_button(btn_frame,
                    "🚨  Regeneración de Emergencia",
                    self._regen_emergencia,
                    bg=COLOR_RED, fg="white",
                    width=30, height=2,
                    font=("Helvetica", 12, "bold")).pack(pady=4)

        nav = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(100, 445, window=nav)
        make_button(nav, "← Nivel 2", self.mostrar_nivel2,
                    bg="#222233", width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)
        make_button(nav, "Nivel 4 →", self.mostrar_nivel4,
                    bg="#440000", fg=COLOR_RED, width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)

        self._blink_amber_n3()
        beep_short(count=5)

    def _draw_amber_n3(self):
        c = self._amber_canvas_n3
        cx, cy, r = self._amber_cx3, self._amber_cy3, self._amber_r3
        on = self._amber_on_n3
        fill_c = COLOR_AMBER if on else COLOR_AMBER_DIM
        c.delete("amber_light_n3")
        if on:
            c.create_oval(cx-r-5, cy-r-5, cx+r+5, cy+r+5,
                          fill="", outline=COLOR_AMBER, width=2,
                          tags="amber_light_n3")
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      fill=fill_c, outline="#333", width=2,
                      tags="amber_light_n3")
        c.create_text(cx, cy+r+12, text="DPF CRIT",
                      fill=COLOR_AMBER if on else COLOR_GRAY,
                      font=("Helvetica", 8), tags="amber_light_n3")

    def _blink_amber_n3(self):
        if self._current_screen != "nivel3":
            return
        self._amber_on_n3 = not self._amber_on_n3
        self._draw_amber_n3()
        self._blink_after = self.after(400, self._blink_amber_n3)

    def _regen_emergencia(self):
        self._mostrar_regenerando(
            titulo="Regeneración de Emergencia",
            mensaje="⚠  Proceso de emergencia activo.\n"
                    "Temperatura del DPF ≥ 600 °C.\n"
                    "Permanezca alejado del escape.\n"
                    "Tiempo estimado: ~25 minutos.",
            duracion_seg=5,
            callback=self._regen_exitosa,
            color_barra=COLOR_RED,
        )

    # ─────────────────────────────────────────
    # PANTALLA 5: NIVEL 4 (>100% — CRÍTICO)
    # ─────────────────────────────────────────
    def mostrar_nivel4(self):
        self._clear()
        self._current_screen = "nivel4"

        # Fondo rojo oscuro para nivel crítico
        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg="#0d0000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Cabecera roja
        canvas.create_rectangle(0, 0, SCREEN_W, 60, fill="#1a0000", outline="")
        canvas.create_line(0, 60, SCREEN_W, 60, fill=COLOR_RED, width=2)
        draw_logo_cocacola_femsa(canvas, 110, 30, scale=0.75)
        canvas.create_text(SCREEN_W // 2 + 30, 20,
                           text="NIVEL 4 — FALLO CRÍTICO DPF",
                           fill=COLOR_RED, font=("Helvetica", 14, "bold"))
        canvas.create_text(SCREEN_W // 2 + 30, 42,
                           text="Saturación > 100%  |  Intervención técnica requerida",
                           fill="#cc4444", font=("Helvetica", 9))

        # Barra saturación > 100%
        draw_saturation_bar(canvas, 440, 95, 320, 28, 105, color=COLOR_RED)
        canvas.create_text(SCREEN_W // 2 + 95, 80,
                           text="SATURACIÓN DPF",
                           fill=COLOR_RED, font=("Helvetica", 10, "bold"))

        # Luz STOP (para parpadeo)
        self._stop_canvas = canvas
        self._stop_on = True
        self._draw_stop()

        # Luces amber + red fijas
        draw_warning_light(canvas, 100, 140, COLOR_AMBER,
                           label="DPF", on=True, radius=18)

        # Velocidad limitada
        canvas.create_text(310, 95, text="VEL. LIMITADA",
                           fill=COLOR_RED, font=("Helvetica", 9, "bold"))
        draw_gauge(canvas, 310, 210, 70, 8, 120,
                   label="", unit="km/h", color=COLOR_RED)
        canvas.create_text(310, 295, text="8 km/h MAX",
                           fill=COLOR_RED, font=("Helvetica", 10, "bold"))

        # Mensajes de fallo crítico
        critical_msgs = [
            ("🔴  FALLO CRÍTICO EN EL DPF", COLOR_RED, ("Helvetica", 13, "bold")),
            ("   El vehículo debe detenerse INMEDIATAMENTE", "#ff6666", ("Helvetica", 10, "bold")),
            ("   Velocidad limitada a 8 km/h", "#ff8888", ("Helvetica", 10)),
            ("   Contactar servicio técnico autorizado", "#ffaaaa", ("Helvetica", 10)),
            ("   No intentar regenerar sin asistencia técnica", "#ffaaaa", ("Helvetica", 10)),
            ("   Posible daño al motor y al DPF", "#ff8888", ("Helvetica", 10)),
        ]
        for i, (m, col, fnt) in enumerate(critical_msgs):
            canvas.create_text(490, 110 + i * 24, text=m,
                               fill=col, font=fnt, anchor="w")

        self._footer(canvas,
                     "Nivel 4 · >100% Saturación · Luz roja STOP · Pitido continuo")

        # Botón de contacto técnico + reinicio
        btn_frame = tk.Frame(canvas, bg="#0d0000")
        canvas.create_window(SCREEN_W // 2 + 60, 390, window=btn_frame)
        make_button(btn_frame,
                    "📞  Contactar Servicio Técnico",
                    self._contacto_tecnico,
                    bg="#550000", fg="#ffaaaa",
                    width=30, height=2,
                    font=("Helvetica", 11, "bold")).pack(pady=3)

        nav = tk.Frame(canvas, bg="#0d0000")
        canvas.create_window(90, 445, window=nav)
        make_button(nav, "← Nivel 3", self.mostrar_nivel3,
                    bg="#1a0000", fg=COLOR_RED, width=10, height=1,
                    font=FONT_SMALL).pack(side="left", padx=4)

        # Pitido continuo
        self._beep_stop_event = beep_continuous_start()
        self._blink_stop()

    def _draw_stop(self):
        c = self._stop_canvas
        c.delete("stop_light")
        cx, cy = 200, 145
        on = self._stop_on
        if on:
            pts = []
            for i in range(8):
                angle = math.radians(i * 45 + 22.5)
                pts.extend([cx + 32 * math.cos(angle),
                             cy + 32 * math.sin(angle)])
            c.create_polygon(pts, fill=COLOR_RED,
                             outline="darkred", width=3, tags="stop_light")
            c.create_text(cx, cy, text="STOP",
                          fill="white", font=("Helvetica", 14, "bold"),
                          tags="stop_light")
        else:
            pts = []
            for i in range(8):
                angle = math.radians(i * 45 + 22.5)
                pts.extend([cx + 32 * math.cos(angle),
                             cy + 32 * math.sin(angle)])
            c.create_polygon(pts, fill=COLOR_RED_DIM,
                             outline="#220000", width=3, tags="stop_light")
            c.create_text(cx, cy, text="STOP",
                          fill="#441111", font=("Helvetica", 14, "bold"),
                          tags="stop_light")

    def _blink_stop(self):
        if self._current_screen != "nivel4":
            return
        self._stop_on = not self._stop_on
        self._draw_stop()
        self._blink_after = self.after(500, self._blink_stop)

    def _contacto_tecnico(self):
        self._mostrar_intervencion_tecnica()

    # ─────────────────────────────────────────
    # PANTALLA 6: Intervención Técnica
    # ─────────────────────────────────────────
    def _mostrar_intervencion_tecnica(self):
        self._clear()
        self._current_screen = "tecnico"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="Intervención Técnica — Servicio Especializado")

        # Ícono de herramienta
        canvas.create_text(SCREEN_W // 2, 130,
                           text="🔧", font=("Helvetica", 50))
        canvas.create_text(SCREEN_W // 2, 185,
                           text="SERVICIO TÉCNICO AUTORIZADO",
                           fill=COLOR_WHITE, font=("Helvetica", 16, "bold"))

        info = [
            "El DPF ha superado el umbral crítico.",
            "Se requiere limpieza o reemplazo del filtro.",
            "",
            "Acciones recomendadas:",
            "  1. Remolcar el vehículo al taller certificado.",
            "  2. Diagnóstico OBD con scanner EURO VI.",
            "  3. Limpieza ultrasónica o sustitución del DPF.",
            "  4. Reseteo de la ECU y verificación de sensores.",
        ]
        for i, line in enumerate(info):
            color = COLOR_AMBER if line.startswith("Acciones") else COLOR_WHITE
            canvas.create_text(SCREEN_W // 2, 220 + i * 22,
                               text=line, fill=color,
                               font=("Helvetica", 10 if line.startswith(" ") else 11))

        self._footer(canvas, "Intervención técnica completada — listo para reiniciar")

        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2, 435, window=btn_frame)
        make_button(btn_frame,
                    "↺  Reiniciar Simulador",
                    self.mostrar_inicio,
                    bg=COLOR_GREEN, fg="white",
                    width=26, height=2,
                    font=("Helvetica", 13, "bold")).pack()

    # ─────────────────────────────────────────
    # PANTALLA: Regenerando (progreso)
    # ─────────────────────────────────────────
    def _mostrar_regenerando(self, titulo, mensaje, duracion_seg,
                              callback, color_barra=COLOR_GREEN):
        self._clear()
        prev_screen = self._current_screen
        self._current_screen = "regenerando"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle=titulo)

        # Ícono de proceso
        canvas.create_text(SCREEN_W // 2, 130,
                           text="⚙", font=("Helvetica", 55),
                           fill=color_barra)

        canvas.create_text(SCREEN_W // 2, 195,
                           text=titulo, fill=COLOR_WHITE,
                           font=("Helvetica", 15, "bold"))

        for i, line in enumerate(mensaje.split("\n")):
            canvas.create_text(SCREEN_W // 2, 225 + i * 22,
                               text=line, fill=COLOR_GRAY,
                               font=("Helvetica", 11))

        # Barra de progreso animada
        bar_x, bar_y = 150, 330
        bar_w, bar_h = 500, 28
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h,
                                 fill=COLOR_BORDER, outline=COLOR_GRAY)

        steps = 60
        interval_ms = int(duracion_seg * 1000 / steps)
        self._prog_step = 0
        self._prog_steps = steps
        self._prog_canvas = canvas
        self._prog_bar_x = bar_x
        self._prog_bar_y = bar_y
        self._prog_bar_w = bar_w
        self._prog_bar_h = bar_h
        self._prog_color = color_barra
        self._prog_callback = callback

        self._update_progress(interval_ms)

        self._footer(canvas, "Regeneración en curso — no apague el motor")

    def _update_progress(self, interval_ms):
        if self._current_screen != "regenerando":
            return
        step = self._prog_step
        steps = self._prog_steps
        c = self._prog_canvas

        pct = step / steps
        w = int(self._prog_bar_w * pct)

        c.delete("progress_bar")
        if w > 0:
            c.create_rectangle(
                self._prog_bar_x + 1, self._prog_bar_y + 1,
                self._prog_bar_x + w, self._prog_bar_y + self._prog_bar_h - 1,
                fill=self._prog_color, outline="", tags="progress_bar"
            )
        c.create_text(
            self._prog_bar_x + self._prog_bar_w // 2,
            self._prog_bar_y + self._prog_bar_h // 2,
            text=f"{int(pct * 100)}%", fill="white",
            font=("Helvetica", 12, "bold"), tags="progress_bar"
        )

        self._prog_step += 1
        if self._prog_step <= steps:
            self._blink_after = self.after(
                interval_ms,
                lambda: self._update_progress(interval_ms)
            )
        else:
            self.after(300, self._prog_callback)

    # ─────────────────────────────────────────
    # PANTALLA: Regeneración Exitosa
    # ─────────────────────────────────────────
    def _regen_exitosa(self):
        self._clear()
        self._current_screen = "exitosa"

        canvas = tk.Canvas(self, width=SCREEN_W, height=SCREEN_H,
                           bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._header(canvas, subtitle="Regeneración Completada")

        canvas.create_text(SCREEN_W // 2, 140,
                           text="✔", font=("Helvetica", 70, "bold"),
                           fill=COLOR_GREEN)
        canvas.create_text(SCREEN_W // 2, 225,
                           text="REGENERACIÓN EXITOSA",
                           fill=COLOR_GREEN, font=("Helvetica", 22, "bold"))
        canvas.create_text(SCREEN_W // 2, 260,
                           text="DPF limpio — Sistema operando con normalidad",
                           fill=COLOR_WHITE, font=("Helvetica", 13))

        draw_saturation_bar(canvas, 200, 300, 400, 28, 12, color=COLOR_GREEN)
        canvas.create_text(SCREEN_W // 2, 285,
                           text="Saturación actual", fill=COLOR_GRAY,
                           font=("Helvetica", 9))

        self._footer(canvas, "Proceso de regeneración completado exitosamente")

        btn_frame = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window(SCREEN_W // 2, 420, window=btn_frame)
        make_button(btn_frame,
                    "↺  Volver al Inicio",
                    self.mostrar_inicio,
                    bg=COLOR_GREEN, fg="white",
                    width=22, height=2,
                    font=("Helvetica", 13, "bold")).pack(side="left", padx=8)
        make_button(btn_frame,
                    "Operación Normal →",
                    self.mostrar_operacion_normal,
                    bg=COLOR_BLUE, fg="white",
                    width=22, height=2,
                    font=("Helvetica", 13, "bold")).pack(side="left", padx=8)


# ═══════════════════════════════════════════════════
# Punto de entrada
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    app = SimuladorDPF()
    app.mainloop()
