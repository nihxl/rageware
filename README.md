<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />

# Rageware — RageWare 

## Basic Details
### Team Name: T480

### Team Members
- Team Lead: Subaib AP - [Vimal Jyothi Engineering College]
- Member 2: Nihal Nasim - [Vimal Jyothi Engineering College]

### Project Description
Rageware is an AI-powered digital heckler that actively watches your screen and violently mocks you via Windows toast notifications when you stop working and start procrastinating. 

### The Problem (that doesn't exist)
Productivity apps are way too nice. They give you "streaks," gentle reminders, and supportive notifications. But when you're 4 hours deep into a YouTube rabbit hole while your code sits broken, a gentle reminder isn't enough. You need someone to actively judge you.

### The Solution (that nobody asked for)
Rageware tracks your active window and browser tabs. If it catches you wasting time, it takes a screenshot of your screen, feeds it to a Vision AI (like Gemini or a local LLaVA model), and generates a highly specific, context-aware insult based on exactly what you're looking at. It then slaps that insult onto your screen as a Windows toast notification. It features 4 distinct personalities:
1. **Toxic Friend** (Casual bro energy)
2. **Corporate Manager** (Weaponized passive-aggressiveness)
3. **AI Overlord** (Cold, robotic superiority)
4. **The One Who Gets It** (Dry, quiet devastation)

## Technical Details
### Technologies/Components Used
For Software:
- **Languages:** Python, JavaScript, HTML/CSS
- **Libraries/Tools:** `win11toast`, `websockets`, `google-genai`, `requests`
- **AI Models:** Google Gemini Cloud API (`gemini-3.8-flash`), Local Ollama (`llava`, `gemma4:12b`)
- **Architecture:** Chrome Extension (client) + Python WebSocket Server (backend)

### Implementation
For Software:
# Installation
```bash
# Clone the repository
git clone https://github.com/nihxl/rageware.git
cd rageware

# Install python dependencies
pip install win11toast websockets google-genai requests

# Add your Gemini API Key (if using cloud models)
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

# Run
```bash
# 1. Start the python backend
python main.py

# 2. Load the Chrome Extension
# Go to chrome://extensions/
# Enable "Developer mode"
# Click "Load unpacked" and select the `extension` folder in this repo
```

### Project Documentation
For Software:

# Screenshots
![Dashboard](https://github.com/user-attachments/assets/dashboard-placeholder)
*The Rageware web dashboard where you can track your "rage level" and switch AI personalities.*

![Toast Notification](https://github.com/user-attachments/assets/toast-placeholder.png)
*A Windows 11 Toast notification delivering a highly specific roast based on the user's screen contents.*
bruh
# Diagrams
![Workflow](https://github.com/user-attachments/assets/architecture-placeholder.png)
*Browser extension detects a distracting site -> Python server captures screen -> Vision AI analyzes screen + applies persona -> Generates insult -> Windows Toast pop-up.*

## Team Contributions
- Suhaib AP: Full-stack development (Python Server, AI Integration)
- Nihal Nasim: Full-stack development (Extension, UI/UX)

---

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)
