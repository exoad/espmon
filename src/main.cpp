#include <Arduino.h>

void setup()
{
    Serial.begin(115200);
}

void loop()
{
    Serial.printf("hello from the esp32, up %lu ms\n", millis());
    delay(1000);
}
