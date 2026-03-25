#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup.sh — Configuración del Simulador DPF en Raspberry Pi 4
# Coca-Cola FEMSA · EURO VI · Pantalla táctil IPS DSI 7"
# ─────────────────────────────────────────────────────────────
set -e

echo "======================================================"
echo " Simulador DPF — Instalación en Raspberry Pi 4"
echo "======================================================"

# 1. Actualizar el sistema
echo "[1/5] Actualizando el sistema..."
sudo apt-get update -y

# 2. Instalar Python3 y Tkinter
echo "[2/5] Instalando Python3 y Tkinter..."
sudo apt-get install -y python3 python3-tk python3-pip

# 3. Instalar herramienta de sonido (para pitidos)
echo "[3/5] Instalando herramienta de audio..."
sudo apt-get install -y alsa-utils beep || true
# Agregar el módulo pcspkr si no está cargado
sudo modprobe pcspkr 2>/dev/null || true

# 4. Configurar el simulador para arranque automático con la pantalla táctil
echo "[4/5] Configurando arranque automático..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$AUTOSTART_DIR/simulador-dpf.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Simulador DPF
Exec=python3 $SCRIPT_DIR/simulador_dpf.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "   Archivo de arranque creado en: $AUTOSTART_DIR/simulador-dpf.desktop"

# 5. Verificar la instalación
echo "[5/5] Verificando la instalación..."
python3 -c "import tkinter; print('   Tkinter OK — versión:', tkinter.TkVersion)"

echo ""
echo "======================================================"
echo " ✔  Instalación completada."
echo ""
echo " Para ejecutar el simulador manualmente:"
echo "   python3 $SCRIPT_DIR/simulador_dpf.py"
echo ""
echo " El simulador se iniciará automáticamente en el"
echo " próximo arranque del sistema."
echo "======================================================"
