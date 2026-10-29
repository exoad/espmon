// The board seam: the Arduino calls the Kira firmware makes.
#pragma once

#include <Arduino.h>

#include "kira/rt.hxx"

namespace board
{
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
}
