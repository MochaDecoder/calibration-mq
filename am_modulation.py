from time import sleep
from datetime import datetime
import json
import random


def setup_am_modulation(FSMR_STD, SigGen_UUC, freq_display, freq_value):
    """Setup FSMR for AM modulation measurements"""

    SigGen_UUC.write_str("SOUR:FREQ:MODE CW")  ### added ###
    SigGen_UUC.write_str(f"SOUR:FREQ:CW {freq_value}")
    SigGen_UUC.write_str("SOUR:POW:LEV:IMM:AMPL 0")
    SigGen_UUC.write_str("OUTP:ALL:STAT ON")  ### added ALL ###
    sleep(5)

    FSMR_STD.write_str("SYST:DISP:UPD ON")
    FSMR_STD.write_str("INST:SEL MREC")
    FSMR_STD.write_str("ROSC:SOUR EXT")
    FSMR_STD.write_str("CALC2:FEED 'XTIM:AM:REL'")
    FSMR_STD.write_str(f"FREQ:CENT {freq_display}")
    sleep(8)

    FSMR_STD.write_str("ADEM:DET:PAV ON")
    FSMR_STD.write_str("ADEM:DET:THD ON")
    FSMR_STD.write_str("ADEM:DET:SINAD ON")
    FSMR_STD.write_str("FILT:HPAS ON")
    FSMR_STD.write_str("FILT:HPAS:FREQ 300 HZ")
    FSMR_STD.write_str("FILT:LPAS ON")
    FSMR_STD.write_str("FILT:LPAS:FREQ 3 KHZ")

    SigGen_UUC.write_str("SOUR:AM:STAT ON")


def perform_am_measurements(
    FSMR_STD, SigGen_UUC, freq_display, freq_value, mod_depths, mqtt_client
):
    """Perform AM modulation measurements for a frequency point"""
    results = []

    # SigGen_UUC.write_str("SOUR:FREQ:MODE CW")  ### added ### ### moved to 10 ###
    # SigGen_UUC.write_str(f"SOUR:FREQ:CW {freq_value}")
    # SigGen_UUC.write_str("SOUR:POW:LEV:IMM:AMPL 0")
    # SigGen_UUC.write_str("OUTP:STAT ON")
    # SigGen_UUC.write_str("SOUR:AM:STAT ON")
    # sleep(5)

    # FSMR_STD.write_str(f"FREQ:CENT {freq_display}") ### moved to 14 ###
    # sleep(8)

    for mod in mod_depths:
        SigGen_UUC.write_str(f"SOUR:AM:DEPT {mod['depth']}")
        sleep(mod["delay"])

        am_value = FSMR_STD.query_float("CALC:MARK:FUNC:ADEM:AM? PAV")
        dist_value = FSMR_STD.query_float("CALC:MARK:FUNC:ADEM:DIST:RES?")

        result = {
            "type": "am_modulation",
            "frequency": freq_display,
            "modDepth": mod["depth"],
            "amValue": round(am_value, 3),
            "distortion": round(dist_value, 3),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        results.append(result)

        if mqtt_client:
            mqtt_client.publish("calibration/am_modulation", json.dumps(result), qos=1)

        sleep(mod["delay"])

    return results


def perform_mock_am_measurements(
    FSMR_STD, SigGen_UUC, freq_display, freq_value, mod_depths, mqtt_client
):
    """Perform mock AM modulation measurements"""
    results = []
    try:
        for mod in mod_depths:
            sleep(mod["delay"] * 0.1)  # Shorter delay for testing

            # Generate mock measurements
            am_value = float(mod["depth"].replace("PCT", "")) + random.uniform(-1, 1)
            dist_value = (
                float(freq_value.replace("e6", "").replace("e9", "000")) / 3000
            ) * random.uniform(1, 5)

            result = {
                "type": "am_modulation",
                "frequency": freq_display,
                "modDepth": mod["depth"],
                "amValue": round(am_value, 2),
                "distortion": round(dist_value, 2),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            results.append(result)

            if mqtt_client:
                mqtt_client.publish(
                    "calibration/am_modulation", json.dumps(result), qos=1
                )
                sleep(0.1)  # Small delay between publications

    except Exception as e:
        print(f"Error in mock AM measurements: {e}")
        raise

    return results
