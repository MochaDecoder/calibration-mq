class MeasurementValidator:
    @staticmethod
    def validate_am_measurement(am_value, distortion):
        """Validate AM measurement values"""
        if not (0 <= am_value <= 100):
            raise ValueError(f"AM value {am_value} out of range (0-100%)")
        if not (0 <= distortion <= 100):
            raise ValueError(f"Distortion value {distortion} out of range (0-100%)")

    @staticmethod
    def validate_level_measurement(level, uncertainty):
        """Validate level measurement values"""
        if not (-150 <= level <= 30):
            raise ValueError(f"Level value {level} out of range (-150 to 30 dBm)")
        if not (0 <= uncertainty <= 3):
            raise ValueError(f"Uncertainty value {uncertainty} out of range (0-3 dB)")


class FrequencyValidator:
    @staticmethod
    def validate_frequency_point(freq_point):
        """Validate frequency point configuration"""
        required_keys = ["display", "value"]
        if not all(key in freq_point for key in required_keys):
            raise ValueError(f"Frequency point missing required keys: {required_keys}")

        # Validate frequency value format
        value = freq_point["value"]
        try:
            float(value.replace("e", "E"))
        except ValueError:
            raise ValueError(f"Invalid frequency value format: {value}")
