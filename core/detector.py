from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.model = YOLO(model_path)
        self.names = self.model.names
        self.device = device

    def detect(self, frame, conf: float = 0.3, imgsz=640):
        results = self.model.predict(
            source=frame,
            imgsz=imgsz,
            conf=conf,
            verbose=False,
            device=self.device
        )
        return results
