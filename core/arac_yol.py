# line_utils.py

import cv2

class Yol:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

class Corridor:
    def __init__(self, giris_yolu: Yol, cikis_yolu: Yol):
        self.entry_line = giris_yolu
        self.exit_line = cikis_yolu
        self.entered_ids = set()
        self.exited_ids = set()
        self.linked_corridors = []  # diğer koridor id'leri (deneysel)


class Yol_Secici:
    def __init__(self):
        self.temp_points = []
        self.corridors = []  # tum koridor ciftleri
        self.step = 0  # 0: entry çiz, 1: exit çiz

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.temp_points) < 2:
                self.temp_points.append((x, y))
                print(f"Point added: {x}, {y}")
            if len(self.temp_points) == 2:
                new_line = Yol(self.temp_points[0], self.temp_points[1])
                if self.step == 0:
                    self.current_entry = new_line
                    self.step = 1
                    print(f"Entry line set: {self.temp_points}")
                else:
                    corridor = Corridor(self.current_entry, new_line)
                    self.corridors.append(corridor)
                    print(f"Exit line set: {self.temp_points} -> Corridor created.")
                    self.step = 0
                self.temp_points = []

    def draw_corridors(self, frame):
        for idx, corridor in enumerate(self.corridors):
            cv2.line(frame, corridor.entry_line.p1, corridor.entry_line.p2, (0, 255, 0), 2)
            cv2.line(frame, corridor.exit_line.p1, corridor.exit_line.p2, (0, 0, 255), 2)
            cv2.putText(frame, f'Corridor {idx+1}', corridor.entry_line.p1,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for point in self.temp_points:
            cv2.circle(frame, point, 5, (255, 0, 255), -1)

    @staticmethod
    def is_crossing_line(curr, prev, line: Yol):
        x, y = curr
        px, py = prev
        x1, y1 = line.p1
        x2, y2 = line.p2

        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2

        sign_curr = A * x + B * y + C
        sign_prev = A * px + B * py + C

        return sign_curr * sign_prev < 0
