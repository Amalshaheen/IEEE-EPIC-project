import RPi.GPIO as GPIO
import time

# Set up GPIO pins
IR_SENSOR_PIN = 17  # The GPIO pin the sensor is connected to

# Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set the sensor pin as an input
GPIO.setup(IR_SENSOR_PIN, GPIO.IN)

print("IR Sensor Ready...")
print("Press Ctrl+C to exit")

try:
    while True:
        # Read sensor state
        # The sensor output is LOW (0) when it detects an object
        # and HIGH (1) when there is no object.
        if GPIO.input(IR_SENSOR_PIN) == 0:
            print("Object Detected!")
        else:
            print("No Object")
        
        time.sleep(0.5) # Wait for half a second before checking again

except KeyboardInterrupt:
    print("Program stopped")
finally:
    # Clean up GPIO settings
    GPIO.cleanup()