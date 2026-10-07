from ultralytics import YOLO
import cv2
import json
import numpy as np
import time
import threading
import os
from customer_session import CustomerSession
from counter import CustomerCounter


# =========================
# CONFIGURATION
# =========================

MODEL = "yolo11s.pt"

CAMERAS = {
    "1": {
        "name": "CAM1",
        "rtsp": "rtsp://127.0.0.1:8954/cam1",
        "zone": "zones/cam1.json"
    },
    "2": {
        "name": "CAM2",
        "rtsp": "rtsp://127.0.0.1:8954/cam2",
        "zone": "zones/cam2.json"
    },
    "3": {
        "name": "CAM3",
        "rtsp": "rtsp://127.0.0.1:8954/cam3",
        "zone": "zones/cam3.json"
    },
    "4": {
        "name": "CAM4",
        "rtsp": "rtsp://127.0.0.1:8954/cam4",
        "zone": "zones/cam4.json"
    },
    "5": {
        "name": "CAM5",
        "rtsp": "rtsp://127.0.0.1:8954/cam5",
        "zone": "zones/cam5.json"
    },
    "6": {
        "name": "CAM6",
        "rtsp": "rtsp://127.0.0.1:8954/cam6",
        "zone": "zones/cam6.json"
    },
    "7": {
        "name": "CAM7",
        "rtsp": "rtsp://127.0.0.1:8954/cam7",
        "zone": "zones/cam7.json"
    },
    "8": {
        "name": "CAM8",
        "rtsp": "rtsp://127.0.0.1:8954/cam8",
        "zone": "zones/cam8.json"
    }
}

print("")
print("==============================")
print("       PILIH KAMERA")
print("==============================")

for key, camera in CAMERAS.items():
    print(f"{key}. {camera['name']}")

print("==============================")

camera_choice = input("Pilih kamera [1-8]: ").strip()

if camera_choice not in CAMERAS:
    print("ERROR: Pilihan kamera tidak valid.")
    raise SystemExit(1)

CAMERA_CONFIG = CAMERAS[camera_choice]
CAMERA_NAME = CAMERA_CONFIG["name"]
RTSP_URL = CAMERA_CONFIG["rtsp"]
ZONE_FILE = CAMERA_CONFIG["zone"]

if not os.path.exists(ZONE_FILE):
    print(f"ERROR: Zone untuk {CAMERA_NAME} belum tersedia: {ZONE_FILE}")
    raise SystemExit(1)

# Target maksimal inference.
# Bukan berarti kamera dibatasi.
INFERENCE_INTERVAL = 0.05
IMG_SIZE = 384
DEVICE = "cpu"


# =========================
# LOAD YOLO
# =========================

print("Loading YOLO...")
model = YOLO(MODEL)


# =========================
# LOAD CUSTOMER ZONE
# =========================

print("Loading Customer Zone...")

with open(ZONE_FILE, "r", encoding="utf-8") as f:
    zone_data = json.load(f)

zone_points = zone_data.get("customer_zone", [])

if len(zone_points) < 3:
    print("ERROR: Customer Zone minimal 3 titik.")
    raise SystemExit(1)

zone_polygon = np.array(
    zone_points,
    dtype=np.int32
)

print("Customer Zone:")
print(zone_points)


# =========================
# CUSTOMER SESSION
# =========================

sessions = {}


# =========================
# CUSTOMER COUNTER
# =========================

counter = CustomerCounter()

print("")
print("Counter hari ini:", counter.get_total())


# =========================
# SHARED RTSP FRAME
# =========================

latest_frame = None
frame_lock = threading.Lock()

capture_running = True
capture_connected = False


# =========================
# RTSP CAPTURE THREAD
# =========================

def capture_loop():

    global latest_frame
    global capture_running
    global capture_connected

    cap = None

    while capture_running:

        # =========================
        # OPEN RTSP
        # =========================

        if cap is None:

            print("Membuka RTSP...")

            cap = cv2.VideoCapture(
                RTSP_URL,
                cv2.CAP_FFMPEG
            )

            cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

            if not cap.isOpened():

                print(
                    "WARNING: RTSP gagal dibuka. "
                    "Retry 2 detik..."
                )

                cap.release()
                cap = None

                capture_connected = False

                time.sleep(2)

                continue

            capture_connected = True

            print("RTSP berhasil dibuka.")


        # =========================
        # READ FRAME
        # =========================

        ret, frame = cap.read()

        if not ret:

            print(
                "WARNING: Frame RTSP gagal. "
                "Reconnect..."
            )

            capture_connected = False

            cap.release()
            cap = None

            time.sleep(1)

            continue


        # =========================
        # KEEP ONLY LATEST FRAME
        # =========================

        with frame_lock:

            latest_frame = frame


    if cap is not None:

        cap.release()

    capture_connected = False


# =========================
# START CAPTURE THREAD
# =========================

capture_thread = threading.Thread(
    target=capture_loop,
    daemon=True
)

capture_thread.start()


# =========================
# WAIT FOR FIRST FRAME
# =========================

print("Menunggu frame pertama...")

while latest_frame is None:

    if not capture_running:
        break

    time.sleep(0.1)


if latest_frame is None:

    print("ERROR: Tidak mendapatkan frame RTSP.")

    capture_running = False

    capture_thread.join(
        timeout=2
    )

    raise SystemExit(1)


print("")
print("========================================")
print(" CCTV CUSTOMER COUNTING")
print("========================================")
print(f"CAMERA       : {CAMERA_NAME}")
print(f"MODEL        : {MODEL.replace(".pt", "").upper()}")
print("ZONE         : CUSTOMER ZONE")
print("QUALIFY      : 5 MENIT")
print("GRACE TRACK  : 30 DETIK")
print("FRAME MODE   : LATEST FRAME")
print("Tekan Q untuk keluar.")
print("")


# =========================
# MAIN LOOP
# =========================

last_inference_time = 0

last_frame = None

while True:

    # =========================
    # RESET DAILY COUNTER
    # =========================

    counter.reset_today_if_needed()


    # =========================
    # GET LATEST FRAME
    # =========================

    with frame_lock:

        if latest_frame is not None:

            frame = latest_frame.copy()

        else:

            frame = None


    if frame is None:

        time.sleep(0.01)

        continue


    # =========================
    # INFERENCE INTERVAL
    # =========================

    now = time.time()

    if (
        INFERENCE_INTERVAL > 0
        and
        now - last_inference_time
        < INFERENCE_INTERVAL
    ):

        if last_frame is not None:

            cv2.imshow(
                "CCTV Counting - Customer Counter",
                last_frame
            )

        if cv2.waitKey(1) & 0xFF == ord("q"):

            break

        continue


    last_inference_time = now


    # =========================
    # YOLO TRACKING
    # =========================

    results = model.track(
        frame,
        persist=True,
        classes=[0],
        conf=0.40,
        tracker="bytetrack.yaml",
        imgsz=IMG_SIZE,
        device=DEVICE,
        verbose=False
    )


    annotated = frame.copy()


    # =========================
    # DRAW CUSTOMER ZONE
    # =========================

    # =========================
    # PROCESS TRACKED PERSON
    # =========================

    boxes = results[0].boxes

    visible_ids = set()


    if boxes.id is not None:

        ids = boxes.id.int().cpu().tolist()

        xyxy = boxes.xyxy.cpu().numpy()


        for track_id, box in zip(
            ids,
            xyxy
        ):

            visible_ids.add(track_id)

            x1, y1, x2, y2 = map(
                int,
                box
            )


            # =========================
            # FOOT POINT
            # =========================

            foot_x = int(
                (x1 + x2) / 2
            )

            foot_y = int(y2)


            # =========================
            # CHECK ZONE
            # =========================

            inside = cv2.pointPolygonTest(
                zone_polygon,
                (foot_x, foot_y),
                False
            ) >= 0


            # =========================
            # CREATE SESSION
            # =========================

            if track_id not in sessions:

                sessions[track_id] = (
                    CustomerSession(track_id)
                )


            session = sessions[track_id]


            # =========================
            # UPDATE SESSION
            # =========================

            result = session.update(
                inside
            )


            elapsed = result["elapsed"]

            qualified = result["qualified"]

            locked = result["locked"]


            # =========================
            # CUSTOMER COUNTER
            # =========================

            if qualified:

                counter.process_session(
                    track_id,
                    True
                )


            # =========================
            # STATUS
            # =========================

            if locked:

                status = "LOCKED"

                text_color = (
                    0,
                    255,
                    0
                )

            elif inside:

                status = "INSIDE"

                text_color = (
                    0,
                    255,
                    255
                )

            else:

                status = "OUTSIDE"

                text_color = (
                    0,
                    0,
                    255
                )


            # =========================
            # FOOT POINT
            # =========================

            head_x = int((x1 + x2) / 2)
            head_y = int(y1)

            cv2.circle(
                annotated,
                (
                    head_x,
                    head_y
                ),
                5,
                text_color,
                -1
            )


            # =========================
            # TIMER
            # =========================

            if inside:

                total_seconds = int(
                    elapsed
                )

                minutes = (
                    total_seconds // 60
                )

                seconds = (
                    total_seconds % 60
                )

                timer_text = (
                    f"{minutes:02d}:"
                    f"{seconds:02d}"
                )

            else:

                timer_text = "00:00"


            # =========================
            # PERSON LABEL
            # =========================

            label = (
                f"ID {track_id:02d} | "
                f"{status} | "
                f"{timer_text}"
            )


            cv2.putText(
                annotated,
                label,
                (
                    x1,
                    max(
                        y1 - 10,
                        20
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                text_color,
                2
            )


    # =========================
    # HANDLE LOST TRACKS
    # =========================

    for track_id, session in sessions.items():

        if track_id not in visible_ids:

            session.handle_lost_track()


    # =========================
    # BOTTOM STATUS
    # =========================

    total_text = (
        f"QUALIFIED TODAY: "
        f"{counter.get_total()}"
    )

    frame_height = annotated.shape[0]

    status_y1 = max(frame_height - 55, 125)
    status_y2 = frame_height - 25

    cv2.putText(
        annotated,
        total_text,
        (20, status_y1),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (0, 255, 0),
        2
    )

    if capture_connected:

        cv2.putText(
            annotated,
            "RTSP: CONNECTED",
            (20, status_y2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            annotated,
            "RTSP: RECONNECTING",
            (20, status_y2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 0, 255),
            2
        )


    # =========================
    # SAVE LAST ANNOTATED FRAME
    # =========================

    last_frame = annotated


    # =========================
    # SHOW
    # =========================

    cv2.imshow(
        "CCTV Counting - Customer Counter",
        annotated
    )


    # =========================
    # EXIT
    # =========================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =========================
# CLEANUP
# =========================

print("")
print("Menghentikan capture thread...")

capture_running = False

capture_thread.join(
    timeout=2
)

cv2.destroyAllWindows()

print("")
print("========================================")
print(" CUSTOMER COUNTING SELESAI")
print(" TOTAL HARI INI:", counter.get_total())
print("========================================")
















