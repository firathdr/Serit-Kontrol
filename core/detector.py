import torch
from ultralytics import YOLO


def varsayilan_cihaz():
    """CUDA varsa GPU, yoksa CPU. Sabit "cuda" olan surum GPU'suz makinede
    caliasmiyordu."""
    return "cuda" if torch.cuda.is_available() else "cpu"


class ObjectDetector:
    def __init__(self, model_path: str, device: str = None):
        self.model = YOLO(model_path)
        self.names = self.model.names
        self.device = device or varsayilan_cihaz()

    def detect(self, frame, conf: float = 0.3, imgsz=640, iou=0.5):
        results = self.model.predict(
            source=frame,
            classes=[2, 3, 5, 7], #işleme alıncak sınıflar,idler {2: 'car', 3: 'motorcycle',  5: 'bus', 7: 'truck' }
            imgsz=imgsz,
            conf=conf,
            verbose=False,
            device=self.device,
            iou = iou
        )
        return results
