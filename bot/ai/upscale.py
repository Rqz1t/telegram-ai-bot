from pathlib import Path
import cv2
import torch
from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact

# Импортируем правильный путь из конфига
from bot.config import BASE_DIR

class UpscaleService:
    MODEL_NAME = "realesr-general-x4v3.pth"
    SCALE = 4

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Ищем модель в папке models РЯДОМ с ботом
        self.model_path = BASE_DIR / "models" / self.MODEL_NAME

        if not self.model_path.exists():
            # Если не нашли, выводим четкую ошибку в лог
            print(f"❌ ОШИБКА: Файл модели не найден здесь: {self.model_path}")
            raise FileNotFoundError(f"Put the file '{self.MODEL_NAME}' in the 'models' folder next to exe!")

        model = SRVGGNetCompact(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_conv=32,
            upscale=self.SCALE,
            act_type="prelu",
        )

        self.upsampler = RealESRGANer(
            scale=self.SCALE,
            model_path=str(self.model_path),
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=self.device == "cuda",
            device=self.device,
        )

        print(f"✅ AI Model loaded from: {self.model_path}")

    def upscale(self, input_path: str | Path, output_path: str | Path) -> Path:
        input_path = str(input_path)
        output_path = str(output_path)

        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        output, _ = self.upsampler.enhance(img, outscale=self.SCALE)
        cv2.imwrite(output_path, output)

        return Path(output_path)