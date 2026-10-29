#include <Arduino.h>

#include "app.kira.hxx"

void setup()
{
    Serial.begin(115200);
    app::setup();
}

void loop()
{
    app::loop();
}
