import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import json
from datetime import datetime
import pandas as pd
import traceback


class NotificationManager:
    def __init__(self, email_config, sms_config):
        self.email_config = email_config
        self.sms_config = sms_config
        self.summary_data = {
            "start_time": datetime.now(),
            "total_measurements": 0,
            "errors": [],
            "warnings": [],
            "am_measurements": [],
            "level_measurements": [],
        }

    # def send_email(self, subject, body):
    #     try:
    #         msg = MIMEMultipart()
    #         msg["From"] = self.email_config["sender_email"]
    #         msg["Subject"] = subject

    #         # Add text body
    #         msg.attach(MIMEText(body, "plain"))

    #         # Connect to SMTP server
    #         with smtplib.SMTP(
    #             self.email_config["smtp_server"], self.email_config["smtp_port"]
    #         ) as server:
    #             server.starttls()
    #             server.login(
    #                 self.email_config["sender_email"],
    #                 self.email_config["sender_password"],
    #             )

    #             # Send to all recipients
    #             for recipient in self.email_config["recipient_emails"]:
    #                 msg["To"] = recipient
    #                 server.send_message(msg)

    #         print(f"Email notification sent: {subject}")
    #     except Exception as e:
    #         print(f"Failed to send email notification: {e}")
    def send_email(self, subject, body):
        try:
            # Connect to SMTP server
            with smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["sender_email"],
                    self.email_config["sender_password"],
                )

                # Create single message with all recipients in BCC
                msg = MIMEMultipart()
                msg["From"] = self.email_config["sender_email"]
                msg["Subject"] = subject
                # Use first recipient in To field and rest in BCC
                msg["To"] = self.email_config["recipient_emails"][0]
                if len(self.email_config["recipient_emails"]) > 1:
                    msg["Bcc"] = ", ".join(self.email_config["recipient_emails"][1:])

                # Add text body
                msg.attach(MIMEText(body, "plain"))

                # Send email to all recipients at once
                server.send_message(msg)

            print(f"Email notification sent: {subject}")
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            traceback.print_exc()

    def send_sms(self, message):
        try:
            client = Client(
                self.sms_config["twilio_account_sid"],
                self.sms_config["twilio_auth_token"],
            )

            # Send to all notification numbers
            for number in self.sms_config["notification_numbers"]:
                client.messages.create(
                    body=message, from_=self.sms_config["twilio_from_number"], to=number
                )

            print(f"SMS notification sent: {message}")
        except Exception as e:
            print(f"Failed to send SMS notification: {e}")

    def log_error(self, error_msg, stack_trace=None):
        timestamp = datetime.now()
        error_data = {
            "timestamp": timestamp,
            "message": error_msg,
            "stack_trace": stack_trace if stack_trace else traceback.format_exc(),
        }
        self.summary_data["errors"].append(error_data)

        # Send immediate notification for errors
        subject = "❌ Calibration Error Alert"
        body = f"""
Error detected in calibration process:
Timestamp: {timestamp}
Error: {error_msg}
Stack Trace: {error_data['stack_trace']}
        """
        self.send_email(subject, body)
        # self.send_sms(f"Calibration Error: {error_msg}")

    def log_warning(self, warning_msg):
        timestamp = datetime.now()
        warning_data = {"timestamp": timestamp, "message": warning_msg}
        self.summary_data["warnings"].append(warning_data)

    def log_measurement(self, measurement_data, measurement_type):
        self.summary_data["total_measurements"] += 1
        if measurement_type == "am":
            self.summary_data["am_measurements"].append(measurement_data)
        else:
            self.summary_data["level_measurements"].append(measurement_data)

    def generate_summary_report(self):
        end_time = datetime.now()
        duration = end_time - self.summary_data["start_time"]

        # Create summary report
        report = f"""
Calibration Summary Report
-------------------------
Start Time: {self.summary_data['start_time']}
End Time: {end_time}
Duration: {duration}
Total Measurements: {self.summary_data['total_measurements']}

Errors ({len(self.summary_data['errors'])}):
{self._format_error_list()}

Warnings ({len(self.summary_data['warnings'])}):
{self._format_warning_list()}

Measurement Statistics:
{self._generate_measurement_stats()}
        """
        return report

    def _format_error_list(self):
        if not self.summary_data["errors"]:
            return "None"
        return "\n".join(
            [
                f"- {error['timestamp']}: {error['message']}"
                for error in self.summary_data["errors"]
            ]
        )

    def _format_warning_list(self):
        if not self.summary_data["warnings"]:
            return "None"
        return "\n".join(
            [
                f"- {warning['timestamp']}: {warning['message']}"
                for warning in self.summary_data["warnings"]
            ]
        )

    def _generate_measurement_stats(self):
        stats = ""

        # AM Modulation Statistics
        if self.summary_data["am_measurements"]:
            am_df = pd.DataFrame(self.summary_data["am_measurements"])
            stats += "\nAM Modulation Measurements:\n"
            stats += f"Total Points: {len(am_df)}\n"
            stats += f"Average AM Value: {am_df['amValue'].mean():.2f}%\n"
            stats += f"Average Distortion: {am_df['distortion'].mean():.2f}%\n"

        # Level Measurement Statistics
        if self.summary_data["level_measurements"]:
            level_df = pd.DataFrame(self.summary_data["level_measurements"])
            stats += "\nLevel Measurements:\n"
            stats += f"Total Points: {len(level_df)}\n"
            stats += f"Average Level: {level_df['measured'].mean():.2f} dBm\n"
            stats += f"Average Uncertainty: {level_df['uncertainty'].mean():.4f} dB\n"

        return stats

    def send_completion_notification(self):
        report = self.generate_summary_report()

        # Send email with detailed report
        subject = "✅ Calibration Process Complete"
        self.send_email(subject, report)

        # Send SMS with brief summary
        # sms_message = (
        #     f"Calibration completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        #     f"Total measurements: {self.summary_data['total_measurements']}\n"
        #     f"Errors: {len(self.summary_data['errors'])}\n"
        #     f"Warnings: {len(self.summary_data['warnings'])}"
        # )
        # self.send_sms(sms_message)
