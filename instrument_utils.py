from time import sleep
from RsInstrument.RsInstrument import RsInstrument
import paho.mqtt.client as paho
from paho import mqtt
import random


class MockFSMR:
    def __init__(self):
        self.idn_string = "Mock FSMR26"
        self.visa_manufacturer = "Mock Manufacturer"
        self.instrument_options = ["Mock Option 1", "Mock Option 2"]
        self.last_freq = None
        self.last_command = None

    def write_str(self, command):
        self.last_command = command
        sleep(0.1)  # Simulate command delay
        if "FREQ:CENT" in command:
            self.last_freq = command.split()[-1]

    def query_str(self, command):
        if "SYST:ERR?" in command:
            return (
                "No error"
                if random.random() > 0.1
                else "Mock Error: Temperature warning"
            )
        return "Mock Response"

    def query_float(self, command):
        try:
            if "ADEM:AM?" in command:
                # Simulate AM measurement with some variation
                base_value = (
                    float(self.last_command.split()[-1].replace("PCT", ""))
                    if self.last_command
                    else 50
                )
                return base_value + random.uniform(-2, 2)
            elif "ADEM:DIST:RES?" in command:
                # Simulate distortion that increases with frequency
                freq_mhz = float(self.last_freq.split()[0]) if self.last_freq else 100
                return (freq_mhz / 3000) * random.uniform(1, 5)
            elif "CARR:RES?" in command:
                # Simulate level measurement
                return (
                    float(self.last_command.split()[-1]) + random.uniform(-0.5, 0.5)
                    if self.last_command
                    else 0
                )
            elif "CARR:SUNC?" in command:
                # Simulate uncertainty that increases with frequency
                freq_mhz = float(self.last_freq.split()[0]) if self.last_freq else 100
                return (freq_mhz / 3000) * random.uniform(0.1, 0.3)
            return random.uniform(0, 100)
        except Exception as e:
            print(f"Error in query_float: {e}")
            return 0.0

    def close(self):
        pass


class MockSigGen:
    def __init__(self):
        self.idn_string = "Mock Signal Generator"
        self.visa_manufacturer = "Mock Manufacturer"
        self.instrument_options = ["Mock Option 1", "Mock Option 2"]
        self.current_freq = None
        self.current_power = None

    def write_str(self, command):
        sleep(0.1)  # Simulate command delay
        if "FREQ:CW" in command:
            self.current_freq = command.split()[-1]
        elif "POW:LEV:IMM:AMPL" in command:
            self.current_power = command.split()[-1]

    def write(self, command):
        self.write_str(command)

    def query_str(self, command):
        if "SYST:ERR?" in command:
            return "No error" if random.random() > 0.1 else "Mock Error: PLL unlocked"
        return "Mock Response"

    def close(self):
        pass


# Modify instrument_utils.py to include mock functionality
def initialize_instruments(config: object, use_mock: object = True) -> object:
    """Initialize real or mock instruments based on use_mock parameter"""
    if use_mock:
        print("Initializing mock instruments...")
        return MockFSMR(), MockSigGen()
    else:

        try:
            FSMR_STD = RsInstrument(config["fsmr_address"], True, False)
            FSMR_STD.instrument_status_checking = True
            print(f"Visa Manuf :{FSMR_STD.visa_manufacturer}")
            print(f"FSMR Connected: {FSMR_STD.idn_string}")
            print(
                f'Instrument installed options: {",".join(FSMR_STD.instrument_options)}'
            )

            SigGen_UUC = RsInstrument(config["siggen_address"], True, False)
            SigGen_UUC.instrument_status_checking = True
            print(f"Visa Manuf :{SigGen_UUC.visa_manufacturer}")
            print(f"SigGen Connected: {SigGen_UUC.idn_string}")
            print(
                f'Instrument installed options: {",".join(SigGen_UUC.instrument_options)}'
            )

            return FSMR_STD, SigGen_UUC
        except Exception as e:
            print(f"Error initializing instruments: {e}")
            return None, None
        pass


def reset_instruments(FSMR_STD, SigGen_UUC):
    """Reset both instruments to default state"""
    FSMR_STD.write_str("*RST")
    SigGen_UUC.write_str("*RST")

def setup_mqtt_client(config):
    """Initialize MQTT client with configuration"""
    try:
        client = paho.Client(client_id="calibration", protocol=paho.MQTTv5)
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(config["username"], config["password"])
        client.connect(config["broker"], config["port"])
        client.loop_start()
        return client
    except Exception as e:
        print(f"Failed to setup MQTT client: {e}")
        return None
