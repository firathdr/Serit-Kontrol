from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, model_path: str, device: str = "cuda"):

        self.model = YOLO(model_path)
        self.names = self.model.names
        self.focal_length = 615
        self.device = device

    def detect(self, frame, conf: float = 0.5, imgsz=(720, 1280)):

        results = self.model.predict(
            source=frame,
            imgsz=imgsz,  #height,width
            conf=conf,
            verbose=False,
            device=self.device
        )
        return results[0]
