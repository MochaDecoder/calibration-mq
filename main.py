import pyvisa
import random
from RsInstrument.RsInstrument import RsInstrument
import paho.mqtt.client as paho
from paho import mqtt
from datetime import datetime

from config import (
    FREQ_POINTS,
    LEVEL_POINTS,
    MOD_DEPTHS,
    #MOD_DEV,
    EMAIL_CONFIG,
    SMS_CONFIG,
    MQTT_CONFIG,
    INSTRUMENT_CONFIG,
)
from instrument_utils import (
    setup_mqtt_client,
    initialize_instruments,
    reset_instruments,
)
from am_modulation import (
    setup_am_modulation,
    perform_am_measurements,
    perform_mock_am_measurements,
)

from level_measurement import (
    setup_level_measurement,
    perform_level_measurements,
    perform_mock_level_measurements,
)
from notification_manager import NotificationManager
from time import sleep


def run_calibration(use_mock=True):
    """Main calibration routine"""
    notification_manager = NotificationManager(EMAIL_CONFIG, SMS_CONFIG)

    try:
        # Initialize MQTT
        mqtt_client = setup_mqtt_client(MQTT_CONFIG)
        if not mqtt_client:
            notification_manager.log_error("Failed to initialize MQTT client")

        # Initialize instruments
        FSMR_STD, SigGen_UUC = initialize_instruments(
            INSTRUMENT_CONFIG, use_mock=use_mock
        )

        if not FSMR_STD or not SigGen_UUC:
            notification_manager.log_error("Failed to initialize instruments")
            return

        # Open result files
        with open("./AM_MOD_Results.txt", "w") as am_file, open(
            "./LEVEL_Results.txt", "w"
        ) as level_file,  open(
            "./FM_MOD_Results.txt", "w") as fm_file:

            am_file.write("Frequency,AM Modulation (%),Distortion (%),Timestamp\n")
            level_file.write("Frequency,Measured,Uncertainty,Timestamp\n")
            fm_file.write("Frequency,FM Modulation (Hz),Distortion (%),Timestamp\n")

            # Main measurement loop
            for freq in FREQ_POINTS:
                print(f"\nProcessing frequency: {freq['display']}")

                try:
                    # AM Modulation measurements
                    reset_instruments(FSMR_STD, SigGen_UUC)
                    print("Performing AM modulation measurements...")
                    setup_am_modulation(
                        FSMR_STD, SigGen_UUC, freq["display"], freq["value"]
                    )
                    am_results = perform_am_measurements(
                        FSMR_STD,
                        SigGen_UUC,
                        freq["display"],
                        freq["value"],
                        MOD_DEPTHS,
                        mqtt_client,
                    )

                    # Level measurements
                    reset_instruments(FSMR_STD, SigGen_UUC)
                    print("Performing level measurements...")
                    setup_level_measurement(
                        FSMR_STD, SigGen_UUC, freq["display"], freq["value"]
                    )
                    level_results = perform_level_measurements(
                        FSMR_STD,
                        SigGen_UUC,
                        freq["display"],
                        freq["value"],
                        LEVEL_POINTS,
                        mqtt_client,
                    )

                    # Log level measurements
                    for result in level_results:
                        notification_manager.log_measurement(result, "level")
                        level_file.write(
                            f"{result['frequency']},{result['measured']},{result['uncertainty']},{result['timestamp']}\n"
                        )
                        level_file.flush()

                except Exception as e:
                    error_msg = (
                        f"Error processing frequency {freq['display']}: {str(e)}"
                    )
                    notification_manager.log_error(error_msg)
                    continue

    except Exception as e:
        notification_manager.log_error(f"Critical error during calibration: {str(e)}")
    finally:
        # Cleanup
        if "FSMR_STD" in locals():
            FSMR_STD.close()
        if "SigGen_UUC" in locals():
            SigGen_UUC.close()
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

        # Send completion notification
        notification_manager.send_completion_notification()


def run_mock_calibration(use_mock=True):
    """Run calibration with mock data"""
    from config import (
        FREQ_POINTS,
        LEVEL_POINTS,
        MOD_DEPTHS,
        #MOD_DEV,
        EMAIL_CONFIG,
        SMS_CONFIG,
        MQTT_CONFIG,
        INSTRUMENT_CONFIG,
    )
    from notification_manager import NotificationManager
    from instrument_utils import setup_mqtt_client

    notification_manager = NotificationManager(EMAIL_CONFIG, SMS_CONFIG)

    try:
        # Initialize MQTT
        mqtt_client = setup_mqtt_client(MQTT_CONFIG)
        if not mqtt_client:
            notification_manager.log_error("Failed to initialize MQTT client")
            return

        # Initialize mock instruments
        FSMR_STD, SigGen_UUC = initialize_instruments(
            INSTRUMENT_CONFIG, use_mock=use_mock
        )
        print("Mock instruments initialized")

        # Open result files
        with open("./MOCK_AM_MOD_Results.txt", "w") as am_file, open(
            "./MOCK_LEVEL_Results.txt", "w"
            ) as level_file, open(
            "./MOCK_FM_MOD_Results.txt", "w") as fm_file:

            am_file.write("Frequency,AM Modulation (%),Distortion (%),Timestamp\n")
            fm_file.write("Frequency,FM Modulation (Hz),Distortion (%),Timestamp\n")
            level_file.write("Frequency,Measured,Uncertainty,Timestamp\n")

            # Main measurement loop
            for freq in FREQ_POINTS:
                print(f"\nProcessing frequency: {freq['display']}")

                try:
                    # Simulate random failures for testing
                    # if random.random() < 0.1:  # 10% chance of failure
                    #     raise Exception(
                    #         f"Simulated random failure at {freq['display']}"
                    #     )

                    # AM Modulation measurements
                    print("Performing mock AM modulation measurements...")
                    am_results = perform_mock_am_measurements(
                        FSMR_STD,
                        SigGen_UUC,
                        freq["display"],
                        freq["value"],
                        MOD_DEPTHS,
                        mqtt_client,
                    )

                    # Log AM measurements
                    for result in am_results:
                        notification_manager.log_measurement(result, "am")
                        am_file.write(
                            f"{result['frequency']},{result['amValue']},{result['distortion']},{result['timestamp']}\n"
                        )
                        am_file.flush()

                    sleep(1)  # Small delay between measurement types

                    # Level measurements
                    print("Performing mock level measurements...")
                    level_results = perform_mock_level_measurements(
                        FSMR_STD,
                        SigGen_UUC,
                        freq["display"],
                        freq["value"],
                        LEVEL_POINTS,
                        mqtt_client,
                    )

                    # Log level measurements
                    for result in level_results:
                        notification_manager.log_measurement(result, "level")
                        level_file.write(
                            f"{result['frequency']},{result['measured']},{result['uncertainty']},{result['timestamp']}\n"
                        )
                        level_file.flush()

                except Exception as e:
                    error_msg = (
                        f"Error processing frequency {freq['display']}: {str(e)}"
                    )
                    print(error_msg)
                    notification_manager.log_error(error_msg)
                    continue

    except Exception as e:
        error_msg = f"Critical error during mock calibration: {str(e)}"
        print(error_msg)
        notification_manager.log_error(error_msg)
    finally:
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

        # Send completion notification
        notification_manager.send_completion_notification()


if __name__ == "__main__":
    run_calibration(use_mock=False)
    # run_mock_calibration()
