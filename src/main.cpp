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


// update everything
void fullRefresh(char title[50], char artist[80], char timestamp[13], float completion, uint8_t cover[5000]) {

    // digitalWrite(2, HIGH);
    // delay(500);
    // digitalWrite(2, LOW);

    display.setFullWindow();

    display.firstPage();

    do {
        display.fillScreen(GxEPD_WHITE);
    
        display.drawBitmap(20, 36, cover, 200, 200, GxEPD_BLACK); // x, y, image, width, height, colour
        // display.drawRect(20, 36, 200, 200, GxEPD_BLACK); // placeholder
    
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
        display.print(timestamp);

    } while (display.nextPage());


}


// only update progress bar + time text
void partialRefresh(char timestamp[13], float completion) {

    // digitalWrite(25, HIGH);
    // delay(500);
    // digitalWrite(25, LOW);

    display.setPartialWindow(245, 155, 527, 62); // x, y, width, height; should cover prog bar + time text

    display.firstPage();

    do {
        // display.fillScreen(GxEPD_WHITE);

        int progress = round(completion * 527);

        display.drawRect(245, 175, 527, 10, GxEPD_BLACK);      // outline
        display.fillRect(245, 175, progress, 10, GxEPD_BLACK); // progress

        display.setFont(&FreeSansBold9pt7b);
        display.setCursor(245, 215);
        display.print(timestamp);

    } while (display.nextPage());
}



void setup() {

    Serial.begin(115200);

    display.init(115200);
    display.setRotation(0);

    display.setTextColor(GxEPD_BLACK);

    // pinMode(25, OUTPUT);
    // pinMode(2, OUTPUT);

}



#define buffer_size 512
char msg_buffer[buffer_size];
uint16_t msg_index = 0;


void loop() {

    if (Serial.available()) {

        // String doc = Serial.readStringUntil('\n');
        char type = Serial.read();

        if (type == 'S') {

            // partial update

            while (Serial.read() != '|');

            char timestamp[13];

            String timestampStr = Serial.readStringUntil('|');
            timestampStr.toCharArray(timestamp, 13);

            float completion = Serial.parseFloat();

            Serial.read();

            // const char* message_char = doc.c_str();
            // sscanf(message_char, "S|%[^|]|%f", &timestamp, &completion);

            partialRefresh(timestamp, completion);
            // doc = ' ';

        }
        else if (type == 'L') {

            // full update

            char title[50], artist[80], timestamp[13];
            
            while (Serial.read() != '|'); // skip to first important value (title)
            
            String titleStr = Serial.readStringUntil('|');
            titleStr.toCharArray(title, 50);
            
            String artistStr = Serial.readStringUntil('|');
            artistStr.toCharArray(artist, 80);
            
            String timestampStr = Serial.readStringUntil('|');
            timestampStr.toCharArray(timestamp, 13);
            
            float completion = Serial.parseFloat();

            while (Serial.read() != '|');
            uint8_t cover[5000];
            int bytes_read = 0;
            unsigned long timeout = millis() + 5000; // gives up if it takes more than 5 secs

            while (bytes_read < 5000 && millis() < timeout) {
                if (Serial.available()) {
                    cover[bytes_read++] = Serial.read();
                }
            }

            Serial.read();


            // const char *message_char = doc.c_str();
            // sscanf(message_char, "L|%[^|]|%[^|]|%[^|]|%[^|]|%f", &title, &artist, &timestamp, &completion, &cover);

            fullRefresh(title, artist, timestamp, completion, cover);
            // doc = ' ';
        }

    }
}