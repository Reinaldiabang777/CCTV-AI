import json
import os
from datetime import datetime


class CustomerCounter:

    def __init__(self, history_file="customer_history.json"):
        self.history_file = history_file

        self.total_today = 0
        self.qualified_ids = set()

        self.today = datetime.now().strftime("%Y-%m-%d")

        self._load_history()

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("date") != self.today:
                return

            self.total_today = int(data.get("total", 0))
            self.qualified_ids = set(
                data.get("qualified_ids", [])
            )

        except Exception as e:
            print(f"[COUNTER] Gagal membaca history: {e}")

    def _save_history(self):
        data = {
            "date": self.today,
            "total": self.total_today,
            "qualified_ids": list(self.qualified_ids)
        }

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def process_session(self, track_id, qualified):
        """
        Menambah counter hanya ketika session baru
        mencapai status QUALIFIED.
        """

        if not qualified:
            return False

        if track_id in self.qualified_ids:
            return False

        self.qualified_ids.add(track_id)
        self.total_today += 1

        self._save_history()

        print(
            f"[COUNTER] QUALIFIED ID {track_id} "
            f"-> TOTAL HARI INI: {self.total_today}"
        )

        return True

    def get_total(self):
        return self.total_today

    def reset_today_if_needed(self):
        current_date = datetime.now().strftime("%Y-%m-%d")

        if current_date != self.today:
            self.today = current_date
            self.total_today = 0
            self.qualified_ids.clear()
            self._save_history()

    def get_status(self):
        return {
            "date": self.today,
            "total": self.total_today
        }


if __name__ == "__main__":
    print("===== CUSTOMER COUNTER TEST =====")

    counter = CustomerCounter()

    print("Status awal:")
    print(counter.get_status())

    print("")
    print("Test ID 1 qualified...")
    counter.process_session(1, True)

    print("Test ID 1 qualified lagi...")
    counter.process_session(1, True)

    print("Test ID 2 belum qualified...")
    counter.process_session(2, False)

    print("Test ID 2 qualified...")
    counter.process_session(2, True)

    print("")
    print("Status akhir:")
    print(counter.get_status())

    print("")
    print("Test selesai.")
