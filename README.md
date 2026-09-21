# Steam GameVault

> A desktop application for managing and visualizing your Steam library in one place.

Steam GameVault is a Windows desktop application built with Python that synchronizes your Steam library and presents your games, playtime, achievements, recent activity, and Steam reviews through a clean and modern interface.

It also supports **Steam Family libraries**, multiple languages, search, filters, sorting, and pagination.

**Languages:** [English](README.md) · [Español](README.es.md)

---

## 📸 Screenshots

### Initial configuration

![Initial configuration](screenshots/setup.png)

### Empty library

![Empty library](screenshots/empty-library.png)

### Steam library

![Steam library](screenshots/library.png)

---

## ✨ Features

- 🎮 **Steam library synchronization**
- 👨‍👩‍👧‍👦 **Steam Family library support**
- ⏱️ Total playtime and recent playtime
- 🕒 Last played information
- 🏆 Achievement progress
- ⭐ Steam review status
- 📝 Steam review text
- 🔎 Game search
- 🎛️ Library, achievement, review, and activity filters
- ↕️ Multiple sorting options
- 📄 Pagination for large libraries
- 🌎 Spanish, English, and Portuguese interface
- 💾 Local SQLite database
- 🔐 Steam API key kept on the backend
- 🖥️ Windows executable available through GitHub Releases

---

## 🖥️ Interface

The application is designed to provide a compact overview of a large Steam library without requiring the user to open Steam for every piece of information.

The main library displays:

| Column | Description |
|---|---|
| **Game** | Steam game title |
| **Hours** | Total recorded playtime |
| **Last Played** | Most recent play session |
| **Last 2 Weeks** | Recent playtime |
| **Achievements** | Unlocked / total achievements |
| **Reviews** | Review status |
| **Review Text** | User's Steam review |

---

## 🔄 How synchronization works

Steam GameVault uses a small backend service to handle Steam Web API requests while keeping the developer's Steam API key out of the desktop application.

```text
┌──────────────────────┐
│ Steam GameVault      │
│ Windows Desktop App  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ FastAPI Backend      │
│                      │
│ Steam API key        │
│ kept server-side     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Steam services       │
│ Web API / Community  │
└──────────────────────┘
```

The desktop application stores synchronized data locally in SQLite.

Steam Family access uses the user's own Family Access Token. This token is stored locally and is not intended to be published or committed to source control.

---

## 🚀 Download

The recommended way for regular users to install Steam GameVault is through the project's **GitHub Releases**.

**[Download the latest Windows release](../../releases/latest)**

No Python installation is required when using the compiled Windows executable.

> The executable is currently distributed as a Windows `.exe`.

---

## ⚙️ Installation from source

### Requirements

- Windows
- Python 3.10+
- A Steam account
- Git (optional, for cloning the repository)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/SteamGameVault.git
cd SteamGameVault
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file for the backend configuration.

Example:

```env
STEAM_API_KEY=your_steam_api_key
```

**Never commit the real `.env` file to GitHub.**

### 4. Start the backend

```bash
uvicorn backend.main:app --reload
```

### 5. Start the desktop application

Open another terminal and run:

```bash
python app/main.py
```

---

## 🔐 Security

Steam GameVault is designed so that the Steam Web API key is handled by the backend rather than being embedded in the desktop application.

Sensitive configuration files should never be committed to the repository.

The following should remain private:

- `.env`
- Steam API keys
- Steam Family Access Tokens
- Local database files containing personal data

The repository should contain only safe example configuration such as `.env.example`.

---

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Main programming language |
| **CustomTkinter** | Desktop graphical interface |
| **FastAPI** | Backend API |
| **SQLite** | Local data storage |
| **Requests** | HTTP communication |
| **BeautifulSoup** | Steam profile/Community parsing |
| **python-dotenv** | Environment configuration |
| **PyInstaller** | Windows executable packaging |

---

## 📁 Project Structure

```text
SteamGameVault/
├── app/
│   ├── main.py
│   ├── models/
│   ├── services/
│   ├── localization/
│   └── ui/
│
├── backend/
│   ├── main.py
│   └── steam_service.py
│
├── data/
│   └── gamevault.db
│
├── requirements.txt
├── .env.example
├── .gitignore
└── SteamGameVault.spec
```

---

## 🌎 Localization

The application currently supports:

- 🇪🇸 Español
- 🇬🇧 English
- 🇧🇷 Português

The selected language is stored locally and restored when the application is opened again.

---

## 🛠️ Building the Windows executable

The application can be packaged using PyInstaller:

```powershell
python -m PyInstaller --onefile --windowed --name SteamGameVault app/main.py
```

The executable will be generated in:

```text
dist/SteamGameVault.exe
```

The `dist/` directory should not be committed to the source repository. Release binaries can be uploaded directly to GitHub Releases.

---

## 📌 Project Status

Steam GameVault is an actively developed project.

Current functionality includes:

- Steam library synchronization
- Steam Family synchronization
- Achievements
- Reviews
- Playtime statistics
- Search and filtering
- Sorting
- Pagination
- Multi-language interface
- Local data persistence
- Windows executable packaging

---

## 🗺️ Roadmap

Potential future improvements include:

- Automatic Family Token renewal
- More detailed statistics and charts
- Game details and cover artwork
- Improved synchronization caching
- Additional Steam metadata
- Automatic application updates
- Installer packaging
- Expanded localization

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

If you find a problem, please open an issue with:

1. A clear description of the problem
2. Steps to reproduce it
3. Expected behavior
4. Actual behavior
5. Relevant screenshots or logs, if available

---

## 📄 License

Add the project's license here before publishing the repository.

---

**Steam GameVault**  
A personal Steam library management application built with Python.
