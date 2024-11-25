# level_measurement.py
from time import sleep
from datetime import datetime
import json
import random


def setup_level_measurement(FSMR_STD, SigGen_UUC, freq_display, freq_value):
    """Setup FSMR for level measurements"""

    SigGen_UUC.write_str("SOUR:FREQ:MODE CW")
    SigGen_UUC.write(f"SOUR:FREQ:CW {freq_value}")
    SigGen_UUC.write_str("SOUR:POW:LEV:IMM:AMPL 0")
    SigGen_UUC.write_str("OUTP:ALL:STAT ON")

    FSMR_STD.write_str("SYST:DISP:UPD ON")
    FSMR_STD.write_str("INST:SEL MREC")
    FSMR_STD.write_str("ROSC:SOUR EXT")
    FSMR_STD.write_str("SENS:PMET:STAT ON")
    sleep(8)

    FSMR_STD.write_str("UNIT:PMET:POW DBM")
    FSMR_STD.write_str("SYST:COMM:RDEV:PMET:TYPE 'NRVD'")
    FSMR_STD.write_str("CAL:PMET:ZERO:AUTO ONCE; *WAI")
    sleep(20)

    FSMR_STD.write_str("POW:AC:STAT ON")
    FSMR_STD.write(f"FREQ:CENT {freq_display}")

    sleep(8)

    FSMR_STD.write_str("SWE:TIME 1S")
    FSMR_STD.write_str("SENS:POW:AC:AVER:AUTO ON")
    FSMR_STD.write_str("SENS:DET:FUNC NARROW")
    FSMR_STD.write_str("INP:ATT:REC:AUTO:STAT ON")

    FSMR_STD.write(f"FREQ:CENT {freq_display}")
    FSMR_STD.write_str("CORR:COLL PSPL")
    sleep(31)

    SigGen_UUC.write_str("SOUR:FREQ:MODE CW")
    SigGen_UUC.write(f"SOUR:FREQ:CW {freq_value}")
    SigGen_UUC.write_str("OUTP:ALL:STAT ON")


def perform_level_measurements(
    FSMR_STD, SigGen_UUC, freq_display, freq_value, level_points, mqtt_client
):
    """Perform level measurements for a frequency point"""
    results = []

    # FSMR_STD.write_str(f"FREQ:CENT {freq_display}") ### moved to 36 ###
    # FSMR_STD.write_str("CORR:COLL PSPL")
    # sleep(31)

    # SigGen_UUC.write_str("SOUR:FREQ:MODE CW") ### moved to 12 ###
    # SigGen_UUC.write_str(f"SOUR:FREQ:CW {freq_value}")
    # SigGen_UUC.write_str("OUTP:ALL:STAT ON")

    for point in level_points:
        SigGen_UUC.write(f"SOUR:POW:LEV:IMM:AMPL {point['level']}")
        sleep(point["delay"])

        level = FSMR_STD.query_float("CALC:MARK:FUNC:ADEM:CARR:RES?")
        uncertainty = FSMR_STD.query_float("CALC:MARK:FUNC:ADEM:CARR:SUNC?")

        result = {
            "type": "level_measurement",
            "frequency": freq_display,
            "level": point["level"],
            "measured": round(level, 3),
            "uncertainty": round(uncertainty, 4),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        results.append(result)

        if mqtt_client:
            mqtt_client.publish(
                "calibration/level_measurement", json.dumps(result), qos=1
            )
        sleep(point["delay"])

    return results


def perform_mock_level_measurements(
    FSMR_STD, SigGen_UUC, freq_display, freq_value, level_points, mqtt_client
):
    """Perform mock level measurements"""
    results = []
    try:
        for point in level_points:
            sleep(point["delay"] * 0.1)  # Shorter delay for testing

            # Generate mock measurements
            base_level = float(point["level"])
            measured_level = base_level + random.uniform(-0.3, 0.3)
            uncertainty = (
                float(freq_value.replace("e6", "").replace("e9", "000")) / 3000
            ) * random.uniform(0.1, 0.3)

            result = {
                "type": "level_measurement",
                "frequency": freq_display,
                "level": point["level"],
                "measured": round(measured_level, 3),
                "uncertainty": round(uncertainty, 4),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            results.append(result)

            if mqtt_client:
                mqtt_client.publish(
                    "calibration/level_measurement", json.dumps(result), qos=1
                )
                sleep(0.1)  # Small delay between publications

    except Exception as e:
        print(f"Error in mock level measurements: {e}")
        raise

    return results
