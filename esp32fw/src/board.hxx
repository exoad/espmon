// The board seam: the Arduino calls esp32/src/board.kira declares to Kira.
#pragma once

#include <Arduino.h>

#include <optional>

#include "kira/rt.hxx"

namespace esp32::board
{
  inline constexpr std::int32_t LED_PIN = 2;
  inline constexpr std::int32_t BOOT_PIN = 0;

  inline void log(const kira::Str& text)
  {
      Serial.println(text.c_str());
  }

  [[nodiscard]] inline std::int32_t millis()
  {
      return static_cast<std::int32_t>(::millis());
  }

  inline void sleep(std::int32_t ms)
  {
      ::delay(static_cast<std::uint32_t>(ms));
  }

  inline void led(bool on)
  {
      ::pinMode(LED_PIN, OUTPUT);
      ::digitalWrite(LED_PIN, on ? HIGH : LOW);
  }

  // The BOOT button pulls its pin low.
  [[nodiscard]] inline bool button()
  {
      ::pinMode(BOOT_PIN, INPUT_PULLUP);
      return ::digitalRead(BOOT_PIN) == LOW;
  }

  [[nodiscard]] inline float temperatureC()
  {
      return ::temperatureRead();
  }

  [[nodiscard]] inline std::int32_t freeHeap()
  {
      return static_cast<std::int32_t>(ESP.getFreeHeap());
  }

  // One byte from the USB serial, none when nothing is waiting.
  [[nodiscard]] inline std::optional<std::uint8_t> readByte()
  {
      const int b = Serial.read();
      return b < 0 ? std::nullopt : std::optional<std::uint8_t>(static_cast<std::uint8_t>(b));
  }
}
