# Synapse Command Deck (Made for Linux)

**Synapse Command Deck** is **not** a generic remapper.  
It is a **high-performance, dedicated engine** designed specifically for a **12-button + 2-knob composite macro pad on Linux**.

It transforms this specific hardware into a **professional productivity powerhouse** with a sleek **Cyberpunk-style UI**, **integrated app search**, and **custom script deployment**.

![Synapse Command Deck UI](https://github.com/user-attachments/assets/fefc481f-1ec7-4899-8a36-b38428621007)


<img width="999" height="801" alt="image" src="https://github.com/user-attachments/assets/1f822485-78d2-44c2-aadf-e8d9f7cfa6c6" /> 
<img width="938" height="817" alt="image" src="https://github.com/user-attachments/assets/455d5908-3f71-48f4-ac4d-432bf02f6fe4" />
<img width="841" height="275" alt="image" src="https://github.com/user-attachments/assets/06534913-0a40-48dc-8a1f-b9dfbd36cd11" />



---

## ✨ Features for the Macro Pad

- 🎯 **Precise 12-Key Mapping**  
  Every key on the 3×4 grid is independently programmable.

- 🔄 **Dual Rotary Dial Automation**  
  Full support for the two rotary encoders (**R1 & R2**) for specialized tasks or volume control.

- 🚀 **Instant App Launcher**  
  Search and link any installed Linux application directly to a specific button on your pad.

- 📜 **Script Deployment**  
  Write and execute Bash scripts directly from your macro pad buttons.

- 📥 **Stealth Mode**  
  Minimizes to the System Tray to keep your desktop clean while the pad remains active in the background.

- 🛡️ **Low-Latency Input**  
  Built on **evdev** to intercept raw hardware events from the pad’s specific **Vendor ID (1189:8840)**.

---

## 🛠️ Installation

### 1️⃣ Prerequisites

Install Python 3 and the required system libraries:

```bash
sudo apt update
sudo apt install python3-pip python3-pyqt5 evdev
```

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/supremelucifer/Synapse-Command-Deck-.git
cd synapse-macro-deck
```

---

### 3️⃣ First Launch

Run the controller with **sudo** to initialize the hardware listener:

```bash
sudo python3 synapse_deck.py
```

---

## 📖 Complete Hardware Setup

This software is designed to work seamlessly with your pad after a **one-time setup**.

To get the **Full Experience**  
*(no passwords, auto-start, and tray applet)* follow the **Internal Setup Guide**:

1. Open the **Synapse** app  
2. Click the **⚙️ SETUP / INFO** button  
3. The app will provide **copy-pasteable commands** tailored to your system to:

   - Correctly identify the `/dev/input/by-id/` path for your pad  
   - Configure **visudo** for passwordless macro execution  
   - Set up the **background start script**  
   - Create a **Desktop Launcher**

---

## ⚡ Designed for One Device. Built to Dominate.

Synapse Command Deck is engineered **exclusively** for this macro pad.  
No abstractions. No compromises.

**Just raw speed, control, and precision — the way a macro engine should be.**
