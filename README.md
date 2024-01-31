# IoT Coffee Machine Project

This project utilizes an ESP8266 microcontroller to measure weight and temperature data, which is then sent to an API for remote monitoring. Below, you'll find an overview of the main objectives and features of this code.

## Features:

1. **Sensors**: The code employs an HX711 weight sensor and a temperature sensor to measure weight and temperature readings, respectively. The weight sensor measures the weight inside a jug, while the temperature sensor records temperature data.

2. **Data Storage**: Measured weight and temperature data are stored in a data structure (struct) and temporarily held in a queue. This prevents data loss during network disruptions.

3. **WiFi Connection**: The ESP8266 establishes a connection to a wireless network via WiFi. It uses the provided SSID and password to connect to the WiFi network.

4. **Ping Function**: The `ping` function sends a ping request to a specified API address and checks whether the connection is successful. If the connection fails, it activates the connection error LED.

5. **Data Transmission**: The measured data is sent to the specified API address via an HTTP POST request. The code takes precautions against connection errors, and unsent data is added to a queue for later transmission.

6. **Data Storage and Resending**: If the data transmission fails due to a connection error, the unsent data is added to a queue and resending is attempted later. Additionally, data transmission occurs periodically at specific intervals.

7. **LED Indicators**: Various LED indicators are used to represent hardware statuses, such as connection status, weight status, and temperature status. These indicators provide visual feedback.

8. **Weight and Temperature Thresholds**: Weight measurements trigger a red warning LED if they exceed a certain threshold, and temperature measurements trigger a warning if they fall below a specified temperature threshold. This warns users when the coffee jug is full and the temperature is not ideal.

9. **Timing**: Measurements are taken at specific intervals, and data is transmitted at regular intervals. Ping requests are also sent at defined intervals.

10. **EEPROM Usage**: The code optionally enables or disables the use of EEPROM, a type of non-volatile memory. EEPROM can be used to store data permanently, preventing data loss.

This code serves as a foundation for an IoT device that monitors weight and temperature data, sending it to a remote server. It can be applied to various scenarios, such as monitoring the coffee level and temperature in a coffee machine.

Feel free to adapt and use this code for your own IoT projects or coffee-related applications.

## Getting Started

Follow these steps to get started with this IoT Coffee Machine project:

1. Hardware Setup: Connect the HX711 weight sensor, temperature sensor, and LEDs to your ESP8266 board following the provided pin assignments.

2. WiFi Configuration: Replace the `ssid` and `password` variables in the code with your WiFi network's SSID and password.

3. API Integration: Configure the `apiUrl`, `apiPort`, `apiSensorEndpoint`, and `apiPingEndpoint` variables to point to your API server.

4. Thresholds and Timing: Adjust the weight and temperature thresholds as well as the timing intervals to suit your requirements.

5. Upload Code: Upload the modified code to your ESP8266 board.

6. Monitoring: Monitor the data sent by your device to the API endpoint to keep track of weight and temperature measurements.

7. Enjoy Your IoT Coffee Machine: Your IoT-enabled coffee machine is now ready to provide you with real-time data about your coffee jug's contents and temperature.

Feel free to contribute to or modify this project as needed. Happy coding!
