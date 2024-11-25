from datetime import datetime
import threading
from time import sleep


class InstrumentMonitor:
    def __init__(self, notification_manager):
        self.notification_manager = notification_manager
        self.monitoring = False
        self.monitor_thread = None
        self.instrument_status = {}

    def start_monitoring(self, FSMR_STD, SigGen_UUC):
        """Start monitoring instruments"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(FSMR_STD, SigGen_UUC)
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring instruments"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self, FSMR_STD, SigGen_UUC):
        """Monitor instrument status periodically"""
        while self.monitoring:
            try:
                # Check FSMR status
                fsmr_status = FSMR_STD.query_str("SYST:ERR?")
                if "No error" not in fsmr_status:
                    self.notification_manager.log_warning(f"FSMR Error: {fsmr_status}")

                # Check SigGen status
                siggen_status = SigGen_UUC.query_str("SYST:ERR?")
                if "No error" not in siggen_status:
                    self.notification_manager.log_warning(
                        f"SigGen Error: {siggen_status}"
                    )

                # Update status
                self.instrument_status = {
                    "timestamp": datetime.now(),
                    "FSMR": fsmr_status,
                    "SigGen": siggen_status,
                }

            except Exception as e:
                self.notification_manager.log_error(f"Monitor error: {str(e)}")

            sleep(30)  # Check every 30 seconds
