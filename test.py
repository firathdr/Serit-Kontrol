import cv2
from ultralytics import YOLO
#from core.detector import ObjectDetector

model_path = "models/yolov8s.pt"
video_path = "videos/video1.mp4"

cap = cv2.VideoCapture(video_path)
model = YOLO(model_path)  # veya yolov8s.pt

#detector = ObjectDetector(model_path)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    fps = cap.get(cv2.CAP_PROP_FPS)
    results = model(frame)
    annotated_frame = results[0].plot()
    resized_frame = cv2.resize(annotated_frame, (1920, 1080))
    cv2.putText(
        resized_frame,  # Üzerine yazılacak görüntü
        str(fps),  # Yazılacak metin
        (10, 30),  # Yazının başlangıç koordinatları (x, y)
        cv2.FONT_HERSHEY_SIMPLEX,  # FONT TYPE (Hatalı: 2 yerine bu)
        1,  # Yazı boyutu (scale)
        (255, 0, 0),  # Renk (BGR)
        2,  # Kalınlık
        cv2.LINE_AA  # Çizim tipi (antialias)
    )
    cv2.imshow("YOLOv8", resized_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()