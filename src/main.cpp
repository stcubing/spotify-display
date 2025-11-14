#include <Arduino.h>
#include <ArduinoJson.h>
#include <LittleFS.h>

void setup() {
    // set up eink stuff here
    Serial.begin(9600); // make sure to send messages through this baud

    pinMode(2, OUTPUT);

    Serial.println("running");
}

void loop() {

    if (Serial.available()) {

        String message = Serial.readStringUntil('\n');
        Serial.println("received " + message);

        if (message.substring(0,6) == "[time]") {
            // partial update

            digitalWrite(2, HIGH);

        } else {
            // full update

            digitalWrite(2, LOW);
        }
        
        
    }

    // Serial.println("periodic message");
    // delay(1000);


}

// #include <Arduino.h>

// void setup() {
//     Serial.begin(115200);
//     pinMode(5, OUTPUT);

// }
// void loop() {
//     Serial.print("ALSKDJJLAKSDADJLSK:DJALSKADS");
//     digitalWrite(5, HIGH);
//     delay(1000);
//     digitalWrite(5, LOW);
//     delay(1000);

// }