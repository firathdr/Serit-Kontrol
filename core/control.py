import cv2

class KeyboardController:
    def __init__(self, cap, fps, skip_seconds=5):
        self.cap = cap
        self.fps = fps
        self.skip_seconds = skip_seconds
        self.speech_enabled = True
        self.paused = False
        self.draw_lines = False
####SİLİNEBİLİR DOSYA
    def check_key(self):
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            return 'quit'
        elif key == ord('p'):
            self.paused = not self.paused
            print("Video durduruldu." if self.paused else "Video başlatıldı.")
        elif key == ord('f'):
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + self.fps * self.skip_seconds)
            print(f"İleri sarıldı")
        elif key == ord('b'):
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            new_frame = max(current_frame - self.fps * self.skip_seconds, 0)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            print(f"Geriye sarıldı.")

        return None
