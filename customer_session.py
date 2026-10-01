import time


QUALIFY_SECONDS = 5 * 60

# Toleransi ketika tracker kehilangan person sementara.
# Selama belum melewati waktu ini, session tetap dianggap berjalan.
TRACK_LOST_GRACE_SECONDS = 30


class CustomerSession:

    def __init__(self, track_id):
        self.track_id = track_id

        self.inside = False
        self.entered_at = None

        self.qualified = False
        self.locked = False

        # Waktu terakhir person masih terdeteksi
        self.last_seen = None

    def update(self, inside):
        now = time.time()

        # Person terlihat lagi
        self.last_seen = now

        # =========================
        # MASUK CUSTOMER ZONE
        # =========================
        if inside and not self.inside:

            self.inside = True
            self.entered_at = now

            print(
                f"[SESSION] ID {self.track_id} "
                f"MASUK ZONE"
            )

        # =========================
        # MASIH DI DALAM ZONE
        # =========================
        if inside:

            if self.locked:
                return {
                    "qualified": False,
                    "locked": True,
                    "elapsed": now - self.entered_at
                }

            elapsed = now - self.entered_at

            # =========================
            # TEMBUS 5 MENIT
            # =========================
            if elapsed >= QUALIFY_SECONDS:

                self.qualified = True
                self.locked = True

                print(
                    f"[QUALIFIED] ID {self.track_id} "
                    f"bertahan >= 5 menit"
                )

                return {
                    "qualified": True,
                    "locked": True,
                    "elapsed": elapsed
                }

            return {
                "qualified": False,
                "locked": False,
                "elapsed": elapsed
            }

        # =========================
        # TERDETEKSI DI LUAR ZONE
        # =========================
        if not inside and self.inside:

            elapsed = 0

            if self.entered_at is not None:
                elapsed = now - self.entered_at

            print(
                f"[SESSION] ID {self.track_id} "
                f"KELUAR ZONE "
                f"(durasi {elapsed:.1f} detik)"
            )

            self.inside = False
            self.entered_at = None

        return {
            "qualified": False,
            "locked": self.locked,
            "elapsed": 0
        }

    def handle_lost_track(self):

        now = time.time()

        # Belum pernah masuk zone
        if not self.inside or self.entered_at is None:
            return {
                "qualified": False,
                "locked": self.locked,
                "elapsed": 0
            }

        # Kalau tracking baru hilang, jangan reset timer
        if self.last_seen is None:
            return {
                "qualified": False,
                "locked": self.locked,
                "elapsed": 0
            }

        lost_for = now - self.last_seen

        # =========================
        # MASIH DALAM GRACE PERIOD
        # =========================
        if lost_for <= TRACK_LOST_GRACE_SECONDS:

            elapsed = now - self.entered_at

            return {
                "qualified": False,
                "locked": self.locked,
                "elapsed": elapsed
            }

        # =========================
        # TRACKING BENAR-BENAR HILANG
        # =========================
        elapsed = now - self.entered_at

        print(
            f"[SESSION] ID {self.track_id} "
            f"TRACK HILANG "
            f"(durasi {elapsed:.1f} detik)"
        )

        self.inside = False
        self.entered_at = None
        self.last_seen = None

        return {
            "qualified": False,
            "locked": self.locked,
            "elapsed": 0
        }

    def get_elapsed(self):

        if not self.inside or self.entered_at is None:
            return 0

        return time.time() - self.entered_at

    def get_remaining(self):

        if self.locked:
            return 0

        elapsed = self.get_elapsed()

        remaining = QUALIFY_SECONDS - elapsed

        if remaining < 0:
            remaining = 0

        return remaining

