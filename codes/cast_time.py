from datetime import datetime, timedelta

CUSTOM_EPOCH_MS = 315964800000
CONVERSION_FACTOR = 1.25 / (256.0 * 256.0)
def convert_timestamp_to_datetime(timestamp):
        """Converts a custom timestamp to a datetime object."""
        date_second = int(timestamp) * CONVERSION_FACTOR + CUSTOM_EPOCH_MS
        unix_timestamp = date_second / 1000  # Convert milliseconds to seconds
        original_datetime = datetime.fromtimestamp(unix_timestamp)

        # Adjust for timezone (+3:30 hours)
        modified_datetime = original_datetime + timedelta(hours=3, minutes=30)

        return modified_datetime
    
print(convert_timestamp_to_datetime(73853194247407624))
