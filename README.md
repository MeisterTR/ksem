# KSEM Smartmeter Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/MeisterTR/ksem?style=flat-square)](https://github.com/MeisterTR/ksem/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/MeisterTR/ksem?style=flat-square)](https://github.com/MeisterTR/ksem/releases)

⚠️ **This integration is currently under active development and not yet production-ready. Use at your own risk.**

---

## 🔧 Purpose

This custom Home Assistant integration provides a local connection to the **KOSTAL Smart Energy Meter (KSEM)** and its attached wallbox(es). It allows real-time monitoring and control via **local REST API** and **WebSocket stream** — no cloud required.

---

## 🚀 Features

- ✅ Local authentication with password
- ✅ REST API communication for configuration and status
- ✅ WebSocket subscription for live charging data
- ✅ Sensor entities:
  - Charging state, phases, current, voltage, power
  - Wallbox device info
  - Energy and load data
- ✅ Control entities:
  - Charging mode (`net`, `pv`, `hybrid`, `locked`)
  - Phase switching (`1-phase`, `3-phase`, `auto`)
  - Battery usage toggle
  - Minimum PV / charging power quota (adjustable)
- 🔄 Automatic updates from WebSocket for live control values
- 🔜 Future: Energy dashboard support

---

## 📁 Installation

### 📦 HACS (custom repository)

> Recommended way to install and keep the component up to date.

1. Open **HACS** in Home Assistant.
2. Go to **Integrations → ⋮ Menu → Custom repositories**.
3. Add this repository:  
   `https://github.com/MeisterTR/ksem`  
   Category: **Integration**
4. After adding, search for **KSEM** and install it.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → + Add Integration**, search for **KSEM**, and follow the setup wizard.

### 🧰 Manual Installation (alternative)

1. Download this repository as ZIP or clone it.
2. Copy the folder `custom_components/ksem/` into your Home Assistant config directory:
   ```bash
   /config/custom_components/ksem/
