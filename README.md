# Simulador de Regeneración DPF — Coca-Cola FEMSA

Simulador visual e interactivo del proceso de regeneración del **Filtro de Partículas Diésel (DPF)** para vehículos con normativa **EURO VI** de la flota Coca-Cola FEMSA.

Desarrollado en **Python / Tkinter** — compatible con **Raspberry Pi 4** y pantalla táctil IPS DSI 7" (800×480 px).

---

## Hardware requerido

| Componente | Especificación |
|---|---|
| SBC | Raspberry Pi 4 Modelo B — 4 GB RAM |
| Almacenamiento | SD 64 GB Clase A2 (SanDisk Extreme) |
| Pantalla | IPS DSI 7" táctil compatible con RPi 4 (800×480) |
| Accesorios | Disipadores de calor, cable DSI, fuente de alimentación 5V/3A |

---

## Flujo del simulador

```
[Inicio]
   │
   ▼
[Operación Normal]  DPF 0–30%  · Sin alertas
   │
   ▼
[Nivel 1]  35–50%  · Luz amarilla FIJA       → Regeneración pasiva / manual
   │
   ▼
[Nivel 2]  70–90%  · Luz amarilla INTERMITENTE → Regeneración manual obligatoria
   │
   ▼
[Nivel 3]  90–100% · Luz amarilla INTERMITENTE + pitidos → Regeneración emergencia
   │
   ▼
[Nivel 4]  >100%   · Luz roja STOP + pitido continuo → Contactar servicio técnico
   │
   ▼
[Intervención Técnica] → [Reiniciar Simulador]
```

---

## Instalación en Raspberry Pi 4

### Opción A — Script automático (recomendado)

```bash
git clone https://github.com/LauraAlonso22/simulacion-dpf.git
cd simulacion-dpf
chmod +x setup.sh
./setup.sh
```

### Opción B — Instalación manual

```bash
# 1. Actualizar el sistema
sudo apt-get update -y

# 2. Instalar dependencias
sudo apt-get install -y python3 python3-tk

# 3. (Opcional) Instalar soporte de audio para pitidos
sudo apt-get install -y alsa-utils beep
sudo modprobe pcspkr

# 4. Ejecutar el simulador
python3 simulador_dpf.py
```

### Arranque automático al encender la Raspberry Pi

El script `setup.sh` configura el arranque automático. También puede hacerse manualmente:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/simulador-dpf.desktop << EOF
[Desktop Entry]
Type=Application
Name=Simulador DPF
Exec=python3 /ruta/al/simulador_dpf.py
EOF
```

---

## Descripción de pantallas

| Pantalla | Saturación | Indicador | Sonido |
|---|---|---|---|
| Inicio / Splash | — | — | — |
| Operación Normal | 0–30% | Todos apagados | — |
| Nivel 1 | 35–50% | Luz amarilla **fija** | — |
| Nivel 2 | 70–90% | Luz amarilla **intermitente** | — |
| Nivel 3 | 90–100% | Luz amarilla **intermitente** | 5 pitidos cortos |
| Nivel 4 | >100% | Luz roja **STOP** + luz ámbar | Pitido continuo |
| Regenerando | — | Barra de progreso | — |
| Regen. Exitosa | ~12% | Check verde | — |
| Intervención Técnica | — | — | — |

---

## Estructura del proyecto

```
simulacion-dpf/
├── simulador_dpf.py   # Código principal del simulador
├── setup.sh           # Script de instalación para Raspberry Pi
├── requirements.txt   # Dependencias Python (ninguna externa requerida)
└── README.md          # Esta documentación
```

---

## Tecnologías

- **Python 3** — sin dependencias externas
- **Tkinter** — interfaz gráfica nativa
- **Canvas** — gráficos vectoriales (gauges, luces, barra DPF, logo)
- **threading** — animaciones y pitidos en segundo plano
- **subprocess** — integración con audio del sistema (beep / aplay)

---

## Licencia

Proyecto de simulación educativa/operativa para Coca-Cola FEMSA.
Simulador de regeneración de DPF para vehículos EURO VI utilizando Raspberry Pi.
