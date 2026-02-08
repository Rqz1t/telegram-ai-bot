import PyInstaller.__main__
import shutil
import os
import basicsr
import realesrgan

# Константы путей
APP_NAME = "MaximusBot"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_PATH = os.path.join(PROJECT_ROOT, "dist", APP_NAME)

# Получаем пути к проблемным библиотекам (для --add-data)
BASIKSR_PATH = os.path.dirname(basicsr.__file__)
REALESRGAN_PATH = os.path.dirname(realesrgan.__file__)

print("🚀 СТАРТ СБОРКИ MAXIMUSBOT (METADATA FIX)...")

# 1. Запуск PyInstaller
PyInstaller.__main__.run([
    'launcher.py',                       
    f'--name={APP_NAME}',                
    '--onedir',                          
    '--noconsole',                       
    '--noconfirm',                       
    '--clean',                           
    
    # Добавляем код бота
    '--add-data=bot;bot',
    
    # === ФИКСЫ ПУТЕЙ (Папки библиотек) ===
    f'--add-data={BASIKSR_PATH};basicsr',       
    f'--add-data={REALESRGAN_PATH};realesrgan', 
    
    # === ФИКСЫ МЕТАДАННЫХ (Лечим твою ошибку PackageNotFoundError) ===
    '--copy-metadata=imageio',     # <--- ВОТ ЭТО ГЛАВНОЕ ЛЕКАРСТВО
    '--copy-metadata=moviepy',     # На всякий случай и для moviepy
    '--copy-metadata=tqdm',        # Часто тоже отваливается, берем сразу
    '--copy-metadata=requests',
    
    # Скрытые импорты
    '--hidden-import=customtkinter',
    '--hidden-import=realesrgan',
    '--hidden-import=basicsr',
    '--hidden-import=imageio',
    '--hidden-import=moviepy',
    
    '--collect-all=customtkinter',
    '--collect-all=torch',
    '--collect-all=torchvision',
    '--collect-all=imageio',       # Забираем всё от греха подальше
])

print("\n✅ EXE СОБРАН. КОПИРУЮ РЕСУРСЫ...")

# 2. КОПИРУЕМ .ENV
source_env = os.path.join(PROJECT_ROOT, ".env")
dest_env = os.path.join(DIST_PATH, ".env")

if os.path.exists(source_env):
    shutil.copy(source_env, dest_env)
    print("   [+] .env скопирован")
else:
    print("   [!] .env не найден!")

# 3. КОПИРУЕМ MODELS
source_models = os.path.join(PROJECT_ROOT, "bot", "models")
dest_models = os.path.join(DIST_PATH, "models")

if os.path.exists(source_models):
    if os.path.exists(dest_models):
        shutil.rmtree(dest_models)
    shutil.copytree(source_models, dest_models)
    print(f"   [+] Папка models перенесена в {dest_models}")
else:
    print(f"   [❌] ОШИБКА: Папка {source_models} не найдена!")

print("-" * 50)
print(f"🎉 ГОТОВО! Пробуй запускать.")