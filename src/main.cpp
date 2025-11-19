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



void setup() {
    
    Serial.begin(9600);
    
    display.init(9600);
    display.setRotation(0);
    
    display.setTextColor(GxEPD_BLACK);
    
    pinMode(25, OUTPUT);
    pinMode(2, OUTPUT);
    
    
}

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

void partialRefresh(String timestamp, double completion) {
    
}

    void loop()
{

    // Serial.println("hello from esp32");

    if (Serial.available())
    {
        String message = Serial.readStringUntil('\n');
        message.trim();

        StaticJsonDocument<400> doc;
        DeserializationError error = deserializeJson(doc, message);

        
        if (error)
        {
            Serial.println("error");
            digitalWrite(25, LOW);
            digitalWrite(2, LOW);
        }
        else
        {

            if (doc["type"] == "small")
            {

                // partial update

                digitalWrite(25, HIGH);
                delay(500);
                digitalWrite(25, LOW);

                // display.setPartialWindow(245, 155, 527, 60); // x, y, width, height; should cover prog bar + time text
            }
            else if (doc["type"] == "large")
            {

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
