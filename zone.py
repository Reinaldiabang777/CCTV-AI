import cv2
import json
import os
import numpy as np

WINDOW_NAME = "CCTV Counting - Set Customer Zone"
ZONE_FILE = "zones.json"

saved_points = []
draft_points = []


def mouse_callback(event, x, y, flags, param):
    global draft_points

    if event == cv2.EVENT_LBUTTONDOWN:
        draft_points.append([x, y])
        print(f"Titik {len(draft_points)}: ({x}, {y})")


def save_zone():
    data = {
        "customer_zone": draft_points
    }

    with open(ZONE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Zone tersimpan ke: {ZONE_FILE}")


def load_zone():
    if not os.path.exists(ZONE_FILE):
        return []

    try:
        with open(ZONE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("customer_zone", [])

    except Exception:
        return []


def draw_zone(frame, points, label):
    if len(points) == 0:
        return frame

    for i, point in enumerate(points):
        x, y = point

        cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)

        cv2.putText(
            frame,
            str(i + 1),
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    if len(points) >= 2:
        for i in range(len(points) - 1):
            cv2.line(
                frame,
                tuple(points[i]),
                tuple(points[i + 1]),
                (0, 255, 0),
                2
            )

    if len(points) >= 3:
        cv2.line(
            frame,
            tuple(points[-1]),
            tuple(points[0]),
            (0, 255, 0),
            2
        )

        overlay = frame.copy()

        polygon = np.array(
            [tuple(point) for point in points],
            dtype=np.int32
        )

        cv2.fillPoly(
            overlay,
            [polygon],
            (0, 255, 0)
        )

        frame = cv2.addWeighted(
            overlay,
            0.20,
            frame,
            0.80,
            0
        )

    cv2.putText(
        frame,
        label,
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    return frame


def main():
    global saved_points, draft_points

    RTSP_URL = "rtsp://127.0.0.1:8954/cam6"

    cap = cv2.VideoCapture(
        RTSP_URL,
        cv2.CAP_FFMPEG
    )

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("ERROR: RTSP tidak bisa dibuka.")
        return

    saved_points = load_zone()
    draft_points = [point[:] for point in saved_points]

    if saved_points:
        print("Zone tersimpan ditemukan:")
        print(saved_points)

    print("")
    print("===== SET CUSTOMER ZONE CAM 6 =====")
    print("Klik kiri : tambah titik")
    print("R         : reset draft")
    print("ENTER     : SET")
    print("S         : SAVE")
    print("Q         : keluar tanpa save")
    print("")

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(
        WINDOW_NAME,
        mouse_callback
    )

    zone_status = "ZONE TERSIMPAN"

    while True:

        ret, frame = cap.read()

        if not ret:
            print("ERROR: gagal membaca RTSP.")
            break

        for _ in range(2):
            cap.grab()

        frame = draw_zone(
            frame,
            draft_points,
            zone_status
        )

        cv2.putText(
            frame,
            "CLICK=POINT | R=RESET | ENTER=SET | S=SAVE | Q=EXIT",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            WINDOW_NAME,
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("r"):
            draft_points.clear()
            zone_status = "DRAFT DI-RESET"
            print("Draft zone di-reset.")

        elif key == 13:
            if len(draft_points) >= 3:
                zone_status = "ZONE DI-SET - BELUM SAVE"
                print("Zone berhasil di-SET. Tekan S untuk menyimpan.")
            else:
                print("Minimal 3 titik diperlukan untuk SET.")

        elif key == ord("s"):
            if len(draft_points) >= 3:
                save_zone()
                saved_points = [point[:] for point in draft_points]
                zone_status = "ZONE TERSIMPAN"
                print("Zone berhasil di-SAVE.")
            else:
                print("Minimal 3 titik diperlukan untuk SAVE.")

        elif key == ord("q"):
            print("Keluar tanpa menyimpan perubahan terakhir.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
