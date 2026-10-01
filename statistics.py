import json
import os
from datetime import datetime


class CustomerStatistics:

    def __init__(self, history_file="customer_history.json"):

        self.history_file = history_file

        self.date = datetime.now().strftime("%Y-%m-%d")

        self.qualified_total = 0

        self.qualified_durations = []

        self.hourly_counts = {}

        self.completed_sessions = 0

        self._load()


    def _load(self):

        if not os.path.exists(self.history_file):
            return

        try:

            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)


            if data.get("date") != self.date:
                return


            self.qualified_total = int(
                data.get("total", 0)
            )

            self.qualified_durations = data.get(
                "qualified_durations",
                []
            )

            self.hourly_counts = data.get(
                "hourly_counts",
                {}
            )

            self.completed_sessions = int(
                data.get("completed_sessions", 0)
            )


        except Exception as e:

            print(
                f"[STATS] Gagal membaca history: {e}"
            )


    def _save(self):

        data = {
            "date": self.date,
            "total": self.qualified_total,
            "qualified_durations":
                self.qualified_durations,
            "hourly_counts":
                self.hourly_counts,
            "completed_sessions":
                self.completed_sessions
        }


        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )


    def record_session(
        self,
        duration,
        qualified
    ):

        self.completed_sessions += 1

        if not qualified:
            self._save()
            return


        self.qualified_total += 1

        self.qualified_durations.append(
            round(duration, 2)
        )


        hour = datetime.now().strftime("%H")


        if hour not in self.hourly_counts:

            self.hourly_counts[hour] = 0


        self.hourly_counts[hour] += 1


        self._save()


    def get_average_dwell(self):

        if not self.qualified_durations:
            return 0


        return (
            sum(self.qualified_durations)
            /
            len(self.qualified_durations)
        )


    def get_hourly_counts(self):

        return self.hourly_counts


    def get_status(self):

        return {
            "date": self.date,
            "qualified_total":
                self.qualified_total,
            "average_dwell":
                self.get_average_dwell(),
            "completed_sessions":
                self.completed_sessions,
            "hourly_counts":
                self.hourly_counts
        }


    def reset_if_new_day(self):

        current_date = datetime.now().strftime(
            "%Y-%m-%d"
        )


        if current_date == self.date:
            return


        self.date = current_date

        self.qualified_total = 0

        self.qualified_durations = []

        self.hourly_counts = {}

        self.completed_sessions = 0

        self._save()
