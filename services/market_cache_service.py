import json
import os
from threading import Lock
import time


class MarketCacheService:

    def __init__(self):
        print("MarketCacheService Instance:", id(self))
        self._lock = Lock()

        self._market_data = []

        self._file_path = "market_snapshot.json"
        
        self._last_save_time = 0

        self._load_from_disk()

    def save(self, data):
        print(f"💾 SAVE CALLED : {len(data)} items")
        with self._lock:

            self._market_data = data.copy()

            current_time = time.time()

            # Save to disk only once every 60 seconds
            if current_time - self._last_save_time >= 60:
                print("📝 Writing market_snapshot.json")
                self._save_to_disk()

                self._last_save_time = current_time
                print("SAVE INSTANCE:", id(self))

    def load(self):

        with self._lock:
            return self._market_data.copy()

    def _save_to_disk(self):

        with open(self._file_path, "w") as file:
            json.dump(self._market_data, file)
        print("✅ JSON SAVED")
        print(os.path.abspath(self._file_path))

    def _load_from_disk(self):

        if not os.path.exists(self._file_path):
            return

        try:

            with open(self._file_path, "r") as file:

                self._market_data = json.load(file)

        except Exception:
            self._market_data = []


market_cache = MarketCacheService()