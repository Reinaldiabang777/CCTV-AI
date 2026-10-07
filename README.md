# CCTV AI Customer Counting

Sistem CCTV AI untuk mendeteksi orang, melakukan tracking, dan menghitung **qualified customer visits** berdasarkan keberadaan seseorang di dalam customer zone selama minimal 5 menit.

Sistem menggunakan YOLO11s, ByteTrack, dan RTSP melalui MediaMTX.

## Fitur

- Person detection menggunakan YOLO11s.
- Mendukung CAM1 sampai CAM8.
- Pemilihan kamera saat program dijalankan.
- RTSP melalui MediaMTX.
- Tracking menggunakan ByteTrack.
- Customer zone berbeda untuk setiap kamera.
- Qualified customer dihitung setelah berada di dalam zone selama minimal 5 menit.
- Satu presence session hanya dihitung satu kali.
- Grace period tracking 30 detik.
- Counter harian otomatis berdasarkan tanggal.
- Tampilan status RTSP dan jumlah qualified customer.
- Latest-frame mode untuk mengurangi delay RTSP.
- Tidak menggunakan ReID atau Unique Customer ID.

## Konsep Counting

Metric yang digunakan adalah **Qualified Customer Visits**, bukan jumlah manusia unik.

Alur counting:

```text
Person terdeteksi
       ↓
Masuk Customer Zone
       ↓
Berada di zone ≥ 5 menit
       ↓
QUALIFIED
       ↓
Counter +1
       ↓
Session LOCKED
```

Jika customer tetap berada di dalam zone setelah qualified, sistem tidak menghitung ulang orang tersebut.

Jika customer keluar dan session berakhir, kemudian kembali masuk ke zone, session baru dapat dihitung.

Sistem **tidak menggunakan ReID** atau Unique Customer ID.

## Setup Awal

### 1. Clone repository

```powershell
git clone https://github.com/Reinaldiabang777/CCTV-AI.git
cd CCTV-AI
```

### 2. Buat virtual environment

```powershell
python -m venv venv
```

Aktifkan virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Jika PowerShell menolak aktivasi karena Execution Policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Install dependency

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Siapkan model YOLO

Model utama yang digunakan:

```text
yolo11s.pt
```

Letakkan model di root project:

```text
CCTV-AI/
└── yolo11s.pt
```

File model tidak disimpan di Git karena file `*.pt` masuk ke `.gitignore`.

### 5. Siapkan MediaMTX

MediaMTX harus berjalan sebelum CCTV AI dijalankan.

CCTV AI menggunakan RTSP:

```text
rtsp://127.0.0.1:8954/cam1
rtsp://127.0.0.1:8954/cam2
rtsp://127.0.0.1:8954/cam3
rtsp://127.0.0.1:8954/cam4
rtsp://127.0.0.1:8954/cam5
rtsp://127.0.0.1:8954/cam6
rtsp://127.0.0.1:8954/cam7
rtsp://127.0.0.1:8954/cam8
```

Pastikan path kamera yang ingin digunakan tersedia di MediaMTX.

### 6. Buat Customer Zone

Jalankan:

```powershell
python zone.py
```

Pilih kamera yang ingin dikonfigurasi, kemudian buat minimal 3 titik untuk menentukan customer zone.

Simpan zone dengan tombol `S`.

Zone disimpan secara terpisah untuk setiap kamera:

```text
zones/cam2.json
zones/cam4.json
zones/cam5.json
zones/cam6.json
zones/cam7.json
zones/cam8.json
```

CAM1 dan CAM3 saat ini belum memiliki zone karena kamera fisiknya belum tersedia atau belum aktif.

### 7. Jalankan Customer Counting

Jalankan:

```powershell
python tracker.py
```

Program akan meminta pilihan kamera:

```text
Pilih kamera [1-8]:
```

Pilih kamera yang ingin digunakan.

Tekan `Q` untuk keluar dari program.

## Arsitektur

```text
NVR
 │
 ▼
MediaMTX
 │
 ├── cam1
 ├── cam2
 ├── cam3
 ├── cam4
 ├── cam5
 ├── cam6
 ├── cam7
 └── cam8
       │
       ▼
   CCTV AI
       │
       ├── YOLO11s
       ├── ByteTrack
       ├── Customer Zone
       ├── Customer Session
       └── Customer Counter
```

## Struktur Project

```text
CCTV-AI/
│
├── tracker.py
├── zone.py
├── counter.py
├── customer_session.py
├── detector.py
├── statistics.py
├── requirements.txt
├── .gitignore
├── yolo11s.pt
│
└── zones/
    ├── cam2.json
    ├── cam4.json
    ├── cam5.json
    ├── cam6.json
    ├── cam7.json
    └── cam8.json
```

> `yolo11s.pt` tidak disimpan di repository Git karena ukurannya besar dan masuk `.gitignore`.

## Menentukan Customer Zone

Gunakan:

```powershell
python zone.py
```

Kontrol:

| Tombol | Fungsi |
|---|---|
| Klik kiri | Menambah titik |
| R | Reset draft zone |
| ENTER | Set zone |
| S | Simpan zone |
| Q | Keluar tanpa menyimpan |

Customer zone membutuhkan minimal 3 titik.

Zone disimpan berdasarkan kamera sehingga setiap kamera dapat memiliki area counting yang berbeda.

## Menjalankan Customer Counting

Gunakan:

```powershell
python tracker.py
```

Sistem kemudian:

1. Membuka RTSP dari MediaMTX.
2. Memuat customer zone sesuai kamera.
3. Menjalankan YOLO11s.
4. Melakukan tracking menggunakan ByteTrack.
5. Memantau keberadaan person di dalam customer zone.
6. Menghitung durasi presence session.
7. Memberikan status `QUALIFIED` setelah 5 menit.
8. Menambahkan counter harian sebesar 1.
9. Mengunci session agar tidak dihitung ulang.

## Status Tampilan

Contoh informasi person:

```text
ID 01 | INSIDE | 03:25
```

Status yang digunakan:

- `INSIDE`: person berada di dalam customer zone.
- `OUTSIDE`: person berada di luar customer zone.
- `LOCKED`: presence session sudah qualified dan tidak dihitung ulang.

Informasi bagian bawah layar:

```text
QUALIFIED TODAY: 3
RTSP: CONNECTED
```

Customer zone ditampilkan sebagai outline tanpa menutupi gambar CCTV.

## Daily Counter

Counter harian disimpan di:

```text
customer_history.json
```

File ini masuk `.gitignore` karena merupakan runtime data.

Counter otomatis di-reset ketika tanggal berubah.

Metric yang disimpan adalah jumlah **qualified customer visits pada hari tersebut**.

## Kamera

| Kamera | MediaMTX | Customer Zone |
|---|---|---|
| CAM1 | cam1 | Belum tersedia |
| CAM2 | cam2 | `zones/cam2.json` |
| CAM3 | cam3 | Belum tersedia |
| CAM4 | cam4 | `zones/cam4.json` |
| CAM5 | cam5 | `zones/cam5.json` |
| CAM6 | cam6 | `zones/cam6.json` |
| CAM7 | cam7 | `zones/cam7.json` |
| CAM8 | cam8 | `zones/cam8.json` |

CAM1 dan CAM3 belum digunakan untuk testing counting karena kamera fisiknya belum aktif.

## Konfigurasi Tracking

```text
Model           : YOLO11s
Confidence      : 0.40
Image Size      : 384
Device          : CPU
Inference Gap   : 0.05 detik
Tracker         : ByteTrack
Track Grace     : 30 detik
Qualification   : 5 menit
```

Tracker menggunakan:

```python
tracker="bytetrack.yaml"
```

Detection hanya menggunakan class person:

```python
classes=[0]
```

## Counting Rules

### Kurang dari 5 menit

Tidak dihitung.

```text
INSIDE
00:00 - 04:59
     ↓
Tidak dihitung
```

### 5 menit atau lebih

Dihitung sebagai qualified customer visit.

```text
INSIDE
05:00+
  ↓
QUALIFIED
  ↓
Counter +1
```

### Tetap berada di zone

Tidak dihitung ulang.

```text
QUALIFIED
    ↓
Tetap di zone 1 jam
    ↓
Tidak ada counter tambahan
```

### Keluar dan kembali

Jika session sebelumnya sudah berakhir, masuk kembali dapat membuat session baru.

```text
Session 1
   ↓
QUALIFIED
   ↓
Keluar
   ↓
Session selesai
   ↓
Masuk kembali
   ↓
Session 2
```

## Tracker Grace Period

Sistem menggunakan grace period selama:

```text
30 detik
```

Tujuannya untuk mencegah session langsung terputus ketika tracking person kehilangan detection sementara.

Dengan demikian, kehilangan detection singkat tidak langsung membuat timer kembali ke nol.

## Troubleshooting

### RTSP tidak terbuka

Periksa:

1. MediaMTX sedang berjalan.
2. Path kamera tersedia.
3. NVR dapat diakses.
4. Kamera yang dipilih memang aktif.
5. URL RTSP sesuai dengan konfigurasi MediaMTX.

### Zone tidak ditemukan

Jika muncul error bahwa zone kamera belum tersedia, jalankan:

```powershell
python zone.py
```

Pilih kamera tersebut dan simpan zone.

### Counting tidak bertambah

Pastikan:

- Person berhasil dideteksi.
- Person berada di dalam customer zone.
- Person tetap berada di zone minimal 5 menit.
- RTSP tidak mengalami disconnect.
- Kamera memiliki sudut pandang yang sesuai dengan customer zone.

### Tracking sering reset

Periksa:

- kualitas RTSP,
- pencahayaan,
- posisi kamera,
- ukuran person pada frame,
- kualitas detection YOLO,
- koneksi NVR dan MediaMTX.

## Development Status

Baseline utama:

```text
Commit: 9496e93
Message: Finalize multi-camera customer counting
```

Baseline tersebut mencakup:

- Multi-camera CAM1-CAM8.
- Customer zone per kamera.
- Customer counting minimum 5 menit.
- Tracker grace period 30 detik.
- Daily counter.
- Latest-frame mode.
- UI cleanup.
- Cleanup file eksperimen dan konfigurasi lama.

## Catatan

Sistem menghitung **qualified customer visits**, bukan jumlah manusia unik.

Hasil counting dapat dipengaruhi oleh:

- kualitas kamera,
- posisi kamera,
- pencahayaan,
- kualitas RTSP,
- person detection,
- tracking,
- bentuk customer zone,
- dan kondisi lingkungan.

Target sistem adalah menjaga perbedaan hasil qualified customer count dengan kondisi aktual tetap seminimal mungkin.

---

## Repository

Source code:

https://github.com/Reinaldiabang777/CCTV-AI
