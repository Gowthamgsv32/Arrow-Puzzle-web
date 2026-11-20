# PyInstaller spec - build with:  pyinstaller assistant.spec --noconfirm
# Output: dist/PersonalAssistant/PersonalAssistant.exe (one-folder build: fast startup)
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = collect_data_files("personal_assistant")
binaries, hiddenimports = [], []

# Packages that ship native libraries or data files PyInstaller can't see on its own.
for pkg in (
    "faster_whisper",  # Silero VAD model
    "ctranslate2",  # Whisper inference engine (DLLs)
    "onnxruntime",
    "tokenizers",
    "av",
    "sounddevice",
    "_sounddevice_data",  # PortAudio DLL (Windows/macOS wheels)
    "soundfile",
    "_soundfile_data",  # libsndfile DLL
    "edge_tts",
    "certifi",
):
    try:
        d, b, h = collect_all(pkg)
    except Exception:
        continue
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["packaging/launcher.py"],
    pathex=["src"],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports + ["personal_assistant.skills.builtin"],
    excludes=[
        "tkinter",
        "matplotlib",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtPdf",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PersonalAssistant",
    icon="packaging/icon.ico",
    console=False,  # windowed app, no black console window
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="PersonalAssistant", upx=False)
