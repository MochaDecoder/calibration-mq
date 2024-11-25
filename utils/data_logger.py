import csv
from datetime import datetime
import os


class DataLogger:
    def __init__(self, base_directory="./logs"):
        self.base_directory = base_directory
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._create_directories()

    def _create_directories(self):
        """Create directory structure for logs"""
        directories = [
            self.base_directory,
            f"{self.base_directory}/am_measurements",
            f"{self.base_directory}/level_measurements",
            f"{self.base_directory}/errors",
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def log_am_measurement(self, data):
        """Log AM measurement data"""
        filename = f"{self.base_directory}/am_measurements/AM_MOD_{self.timestamp}.csv"
        self._write_csv(filename, data)

    def log_level_measurement(self, data):
        """Log level measurement data"""
        filename = (
            f"{self.base_directory}/level_measurements/LEVEL_{self.timestamp}.csv"
        )
        self._write_csv(filename, data)

    def log_error(self, error_data):
        """Log error information"""
        filename = f"{self.base_directory}/errors/errors_{self.timestamp}.txt"
        with open(filename, "a") as f:
            f.write(f"\n[{datetime.now()}] {error_data}\n")

    def _write_csv(self, filename, data):
        """Write data to CSV file"""
        is_new_file = not os.path.exists(filename)
        mode = "w" if is_new_file else "a"

        with open(filename, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if is_new_file:
                writer.writeheader()
            writer.writerow(data)
