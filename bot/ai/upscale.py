from pathlib import Path

import cv2
import torch

from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact


class UpscaleService:
    MODEL_NAME = "realesr-general-x4v3.pth"
    SCALE = 4

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model_path = (
            Path(__file__).resolve().parent.parent / "models" / self.MODEL_NAME
        )

        if not self.model_path.exists():
            raise FileNotFoundError(f"❌ Модель не найдена: {self.model_path}")

        # ✅ ПРАВИЛЬНАЯ архитектура под realesr-general-x4v3
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

        print(f"✅ UpscaleService загружен ({self.device})")

    def upscale(self, input_path: str | Path, output_path: str | Path) -> Path:
        input_path = str(input_path)
        output_path = str(output_path)

        img = cv2.imread(input_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("❌ Не удалось прочитать изображение")

        try:
            output, _ = self.upsampler.enhance(img, outscale=self.SCALE)
        except Exception as e:
            raise RuntimeError(f"❌ Ошибка апскейла: {e}")

        cv2.imwrite(output_path, output)
        return Path(output_path)
