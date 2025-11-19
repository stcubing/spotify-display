#include <Arduino.h>

#include <GxEPD2_BW.h>
#include <Fonts/FreeSans12pt7b.h>
#include <Fonts/FreeSans18pt7b.h>
#include <Fonts/FreeSansBold9pt7b.h>

#include <ArduinoJson.h>



// define display
GxEPD2_BW<GxEPD2_579_GDEY0579T93, GxEPD2_579_GDEY0579T93::HEIGHT> display(
    GxEPD2_579_GDEY0579T93(5, 17, 16, 4) // cs, dc, rst, busy pins
);

String trickleSerialLines(HardwareSerial &serial) {
    static String line;
    int i = line.indexOf('\n');
    if (i > -1)
    {
        String result = line.substring(0, i);
        line = line.substring(i + 1);
        return result;
    }
    if (serial.available())
    {
        String str = serial.readString();
        line += str;
    }
    return "";
}




// update everything
void fullRefresh(String title, String artist, String cover, String timestamp, String duration, double completion) {


    display.setFullWindow();

    display.firstPage();

    do {
        display.fillScreen(GxEPD_WHITE);
    
        // display.drawBitmap(50, 50, smiley_bitmap, 50, 34, GxEPD_BLACK); // x, y, image, width, height, colour
        display.drawRect(20, 36, 200, 200, GxEPD_BLACK); // placeholder
    
        display.setFont(&FreeSans18pt7b);
        display.setTextWrap(false);
        display.setCursor(245, 95);
        display.print(title);
    
        display.setFont(&FreeSans12pt7b);
        display.setCursor(245, 140);
        display.print(artist);

        int progress = round(completion * 527);
    
        display.drawRect(245, 175, 527, 10, GxEPD_BLACK); // outline
        display.fillRect(245, 175, progress, 10, GxEPD_BLACK); // progress
    
        display.setFont(&FreeSansBold9pt7b);
        display.setCursor(245, 215);
        display.print(timestamp + " / " + duration);

    } while (display.nextPage());


}


// only update progress bar + time text
void partialRefresh(String timestamp, String duration, double completion) {

    display.setPartialWindow(245, 155, 527, 62); // x, y, width, height; should cover prog bar + time text

    display.firstPage();

    do {
        display.fillScreen(GxEPD_WHITE);

        int progress = round(completion * 527);

        display.drawRect(245, 175, 527, 10, GxEPD_BLACK);      // outline
        display.fillRect(245, 175, progress, 10, GxEPD_BLACK); // progress

        display.setFont(&FreeSansBold9pt7b);
        display.setCursor(245, 215);
        display.print(timestamp + " / " + duration);

    } while (display.nextPage());
}





void setup() {

    Serial.begin(38400);

    display.init(38400);
    display.setRotation(0);

    display.setTextColor(GxEPD_BLACK);

    pinMode(25, OUTPUT);
    pinMode(2, OUTPUT);
}

void loop() {

    // Serial.println("hello from esp32");

    if (Serial.available()) {
        // String message = trickleSerialLines(Serial);
        String message = Serial.readStringUntil('\n'); // something about this may be causing lag

        StaticJsonDocument<400> doc;
        DeserializationError error = deserializeJson(doc, message);

        
        if (error) {
            digitalWrite(25, LOW);
            digitalWrite(2, LOW);
        }
        else {

            if (doc["type"] == "small") {
                // partial update

                digitalWrite(25, HIGH);
                delay(500);
                digitalWrite(25, LOW);

                String timestamp = doc["timestamp"];
                String duration = doc["duration"];
                double completion = doc["completion"];

                partialRefresh(timestamp, duration, completion);

            }
            else if (doc["type"] == "large") {

                // full update

                digitalWrite(2, HIGH);
                delay(500);
                digitalWrite(2, LOW);

                String title = doc["title"];
                String artist = doc["artist"];
                String cover = doc["cover"];
                String timestamp = doc["timestamp"];
                String duration = doc["duration"];
                double completion = doc["completion"];

                fullRefresh(title, artist, cover, timestamp, duration, completion);
            }
        }
    }
}
