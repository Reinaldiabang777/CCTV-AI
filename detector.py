from ultralytics import YOLO
import cv2

MODEL = "yolo11n.pt"
RTSP_URL = "rtsp://127.0.0.1:8954/cam5"

print("Loading YOLO...")
model = YOLO(MODEL)

print("Membuka RTSP...")
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("ERROR: RTSP tidak bisa dibuka.")
    raise SystemExit(1)

print("RTSP berhasil dibuka.")
print("Tracking aktif.")
print("Tekan Q untuk keluar.")

while True:

    # Buang beberapa frame lama agar latency tidak menumpuk
    for _ in range(3):
        ret, frame = cap.read()

    if not ret:
        print("ERROR: Gagal membaca frame.")
        break

    results = model.track(
        frame,
        persist=True,
        classes=[0],
        conf=0.40,
        tracker="bytetrack.yaml",
        verbose=False
    )

    annotated = results[0].plot()

    # Tampilkan ID temporary tracker
    if results[0].boxes.id is not None:
        ids = results[0].boxes.id.int().cpu().tolist()

        cv2.putText(
            annotated,
            f"Tracked Persons: {len(ids)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "CCTV Counting - Temporary Tracking",
        annotated
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print("Test tracking selesai.")
