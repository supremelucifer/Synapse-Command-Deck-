Synapse Command Deck is not a generic remapper. It is a high-performance, dedicated engine designed specifically for the 12-button + 2-knob composite macro pad on Linux. It transforms this specific hardware into a professional productivity powerhouse with a sleek "Cyberpunk-style" UI, integrated app search, and custom script deployment.

<img width="686" height="386" alt="image" src="https://github.com/user-attachments/assets/fefc481f-1ec7-4899-8a36-b38428621007" />


✨ Features for the Macro Pad

    🎯 Precise 12-Key Mapping: Every key on the 3x4 grid is independently programmable.

    🔄 Dual Rotary Dial Automation: Full support for the two rotary encoders (R1 & R2) for specialized tasks or volume control.

    🚀 Instant App Launcher: Search and link any installed Linux application directly to a specific button on your pad.

    📜 Script Deployment: Write and execute Bash scripts directly from your macro pad buttons.

    📥 Stealth Mode: Minimizes to the System Tray to keep your desktop clean while the pad remains active in the background.

    🛡️ Low-Latency Input: Built on evdev to intercept raw hardware events from the pad's specific Vendor ID (1189:8840).

🛠️ Installation
1. Prerequisites

Install Python 3 and the required system libraries:
code Bash

sudo apt update
sudo apt install python3-pip python3-pyqt5 evdev

2. Clone the Repository
code Bash

git clone https://github.com/YOUR_USERNAME/synapse-macro-deck.git
cd synapse-macro-deck

3. First Launch

Run the controller with sudo to initialize the hardware listener:
code Bash

sudo python3 synapse_deck.py

📖 Complete Hardware Setup

This software is designed to work seamlessly with your pad after a one-time setup. To get the "Full Experience" (no passwords, auto-start, and tray applet), follow the Internal Setup Guide:

    Open the Synapse app.

    Click the ⚙️ SETUP / INFO button.

    The app will provide you with copy-pasteable commands tailored to your system to:

        Correctly identify the /dev/input/by-id/ path for your pad.

        Configure visudo for passwordless macro execution.

        Set up the background start-script and Desktop Launcher.
