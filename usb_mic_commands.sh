# USB Microphone Fix Commands for Raspberry Pi
# Run these commands one by one in your terminal

# Step 1: Check if USB microphone is detected
echo "=== Step 1: Check USB devices ==="
lsusb | grep -i audio
lsusb | grep -i microphone  
lsusb | grep -i webcam

# Step 2: Check ALSA audio cards
echo "=== Step 2: Check audio cards ==="
cat /proc/asound/cards
aplay -l
arecord -l

# Step 3: Test basic recording (replace X with your card number from arecord -l)
echo "=== Step 3: Test recording ==="
# Try default first
arecord -d 3 -f cd test.wav
aplay test.wav

# If default doesn't work, try specific card (usually card 1 for USB)
arecord -D plughw:1,0 -d 3 -f cd test.wav
aplay test.wav

# Step 4: Check and set microphone volume
echo "=== Step 4: Set microphone volume ==="
alsamixer
# In alsamixer:
# - Press F6 to select sound card (choose USB device)
# - Press F4 to show capture devices
# - Use arrow keys to select microphone
# - Press + to increase volume to 80-100%
# - Press M to unmute if it shows "MM"
# - Press Esc to exit

# Step 5: Add user to audio group (if needed)
echo "=== Step 5: Fix permissions ==="
sudo usermod -a -G audio $USER
groups $USER  # Check if audio group is listed

# Step 6: Check permissions
echo "=== Step 6: Check device permissions ==="
ls -la /dev/snd/

# Step 7: Alternative test with different settings
echo "=== Step 7: Alternative tests ==="
# Try different sample rates and formats
arecord -D plughw:1,0 -f S16_LE -r 44100 -d 3 test.wav
aplay test.wav

# Try with different buffer settings
arecord -D plughw:1,0 --buffer-size=4096 -d 3 test.wav  
aplay test.wav

# Step 8: Check PulseAudio (if installed)
echo "=== Step 8: Check PulseAudio ==="
pactl list short sources
pactl list short sinks

# Step 9: Restart audio services
echo "=== Step 9: Restart audio ==="
sudo systemctl restart alsa-state
sudo alsa force-reload

# Step 10: Final test
echo "=== Step 10: Final test ==="
arecord -d 5 -f cd final_test.wav
aplay final_test.wav