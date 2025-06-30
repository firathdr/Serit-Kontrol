import cv2
from core.detector import ObjectDetector
model_path = "models/yolov8s.pt"
video_path = "videos/video1.mp4"

detector = ObjectDetector(model_path, device="cuda")  # cuda veya cpu

cap = cv2.VideoCapture(video_path)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = detector.detect(frame, conf=0.3, imgsz=1920)
    annotated_frame = results[0].plot()

    fps = cap.get(cv2.CAP_PROP_FPS)
    cv2.putText(
        annotated_frame,
        str(str(fps)+ "fps"),
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 0),
        2,
        cv2.LINE_AA
    )
    cv2.imshow("YOLOv8 ", annotated_frame)


    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

