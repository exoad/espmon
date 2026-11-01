"""Mutation tests for the esp32 library: each mutant changes one line of library source, the Kira tests are compiled
and run against it, and a mutant the tests still pass is a survivor, a hole in the tests.

    .venv/Scripts/python tests/mutants.py            run every mutant, print killed, survived and not viable
    .venv/Scripts/python tests/mutants.py frame      only the mutants whose file name contains "frame"

A mutant whose old text is not found exactly once is reported as stale: the source moved and the mutant needs updating.
A mutant that does not compile is not viable and is reported apart from the killed ones. The original file is always
restored, even when the run is stopped.
"""
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KIRA = os.path.join(ROOT, "vendor", "kira", "build", "install", "kira", "bin", "kira.bat")
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
TESTS = os.path.join(ROOT, "tests")

# (file under esp32/src, old text, new text, what the change breaks)
MUTANTS = [
    ("frame.kira", "CRC_POLY: UInt32 = 0x82F63B78", "CRC_POLY: UInt32 = 0xEDB88320", "the CRC polynomial is the wrong one"),
    ("frame.kira", "if payload.size() > MAX_PAYLOAD || payload.size() % 4 != 0 {", "if payload.size() % 4 != 0 {", "encode accepts oversized payloads"),
    ("frame.kira", "if payload.size() > MAX_PAYLOAD || payload.size() % 4 != 0 {", "if payload.size() > MAX_PAYLOAD {", "encode accepts a payload that is not a multiple of 4"),
    ("frame.kira", "crc32c(out, out.size())", "crc32c(out, out.size() - 1)", "the CRC covers one byte too few"),
    ("frame.kira", "(bytes[0] as Int32) != MAGIC_LO || (bytes[1] as Int32) != MAGIC_HI", "(bytes[0] as Int32) != MAGIC_LO", "check ignores the second magic byte"),
    ("frame.kira", "len % 4 != 0 || len > MAX_PAYLOAD ? BAD_LENGTH", "len % 4 != 0 ? BAD_LENGTH", "check accepts an oversized length"),
    ("frame.kira", "n != HEADER_BYTES + len + TRAILER_BYTES ? BAD_LENGTH", "n < HEADER_BYTES + len + TRAILER_BYTES ? BAD_LENGTH", "check accepts trailing bytes"),
    ("frame.kira", "littleEndian(bytes, n - TRAILER_BYTES, 4) ? BAD_CRC", "littleEndian(bytes, n - TRAILER_BYTES, 3) ? BAD_CRC", "check compares a truncated CRC"),
    ("frame.kira", "littleEndian(bytes, 6, 2) as Int32, payload", "littleEndian(bytes, 6, 1) as Int32, payload", "decode reads a one-byte sequence"),
    ("frame.kira", "v = v + ((data[at + i] as Int64) << (8 * i))", "v = v + ((data[at + i] as Int64) << (8 * (i + 1)))", "little-endian reads shift the wrong way"),
    ("frame.kira", "last < 0 || ((seq - last + 65536) % 65536 > 0 && (seq - last + 65536) % 65536 < 32768)", "last < 0 || ((seq - last + 65536) % 65536 > 0 && (seq - last + 65536) % 65536 <= 32768)", "the half-window boundary is off by one"),
    ("link.kira", "if len % 4 != 0 || len > MAX_PAYLOAD {", "if len % 4 != 0 {", "the receiver accepts an oversized length"),
    ("link.kira", "} else if (held[1] as Int32) != MAGIC_HI {", "} else if false {", "the receiver ignores the second magic byte"),
    ("link.kira", "} else if held.size() == 1 {", "} else if held.size() == 0 {", "the receiver checks the magic before it has a byte"),
    ("telemetry.kira", "if f.kind != KIND_TELEMETRY || f.payload.size() != 16 {", "if f.kind != KIND_TELEMETRY {", "decode accepts telemetry of the wrong size"),
    ("telemetry.kira", "littleEndian(f.payload, 8, 4) - TEMP_BIAS", "littleEndian(f.payload, 8, 4)", "temperature is not un-biased"),
    ("telemetry.kira", "leBytes(t.rssiDbm + RSSI_BIAS, 4)", "leBytes(t.rssiDbm, 4)", "signal is not biased on encode"),
    ("telemetry.kira", "encode(KIND_TELEMETRY, 1, seq, body)", "encode(KIND_TELEMETRY, 2, seq, body)", "telemetry is framed as version 2"),
    ("selftest.kira", "failures.size() == 0", "true", "a FAIL line does not make a report not ok"),
    ("selftest.kira", "if parts.size() == 2 {", "if parts.size() == 1 {", "a malformed summary is read anyway"),
    ("selftest.kira", "r.total = parts[1].toInt64().unwrapOr(-1) as Int32", "r.total = parts[0].toInt64().unwrapOr(-1) as Int32", "the total is the passed count"),
    ("ina226.kira", "raw >= 32768 ? raw - 65536 : raw", "raw > 32768 ? raw - 65536 : raw", "the sign boundary is off by one"),
    ("ina226.kira", "shuntUv / rshuntMilliohm", "shuntUv * rshuntMilliohm", "current divides by the wrong thing"),
    ("ina226.kira", "(5120000.0 / (lsbMicroamps * rshuntMilliohm))", "(5120000.0 / lsbMicroamps)", "calibration ignores the shunt"),
    ("ina226.kira", "raw.toFloat64() * 1.25", "raw.toFloat64() * 1.5", "bus voltage uses the wrong LSB"),
    ("sensors.kira", "(raw >= 32768 ? raw - 65536 : raw).toFloat64() / 16.0", "(raw >= 32768 ? raw - 65536 : raw).toFloat64() / 8.0", "the probe scale is doubled"),
    ("sensors.kira", "raw >= 32768 ? raw - 65536 : raw", "raw > 32768 ? raw - 65536 : raw", "the probe sign boundary is off by one"),
    ("ring.kira", "if held.size() >= cap as Size {", "if held.size() > cap as Size {", "the ring grows past its capacity"),
    ("ring.kira", "held.removeAt(0)", "held.removeAt(held.size() - 1)", "the ring drops the newest instead of the oldest"),
    ("lines.kira", "if b != CR && held.size() < cap {", "if b != CR {", "a line is not cut at its cap"),
    ("debounce.kira", "if streak >= need {", "if streak > need {", "a press needs one reading too many"),
    ("command.kira", "n + 1 < parts.size() ? parts[n + 1] : null", "n < parts.size() ? parts[n + 1] : null", "an argument past the last is read"),
]


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def compile_tests():
    return run([KIRA, "--target", "py"], TESTS)


def run_tests():
    return run([PY, os.path.join(TESTS, "esp32_test_kira.py")], ROOT)


def check():
    """Recompiles the tests against the current source and runs them: 'passes', 'killed' or 'not viable'."""
    compiled = compile_tests()
    if compiled.returncode != 0 or "error:" in compiled.stdout + compiled.stderr:
        return "not viable"
    ran = run_tests()
    if ran.returncode != 0:
        return "killed"
    return "passes"


def main(argv):
    filt = argv[0] if argv else ""
    chosen = [m for m in MUTANTS if filt in m[0]]
    base = check()
    if base != "passes":
        print(f"baseline does not pass: {base}; no mutant run")
        return 2
    killed, survived, stale, unviable = [], [], [], []
    for fname, old, new, why in chosen:
        path = os.path.join(ROOT, "esp32", "src", fname)
        with open(path, encoding="utf-8", newline="") as fh:
            original = fh.read()
        if original.count(old) != 1:
            stale.append((fname, why, original.count(old)))
            continue
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(original.replace(old, new, 1))
            result = check()
        finally:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(original)
        if result == "killed":
            killed.append((fname, why))
        elif result == "not viable":
            unviable.append((fname, why))
        else:
            survived.append((fname, why))
    compile_tests()
    print(f"killed {len(killed)}, survived {len(survived)}, not viable {len(unviable)}, stale {len(stale)}, of {len(chosen)}")
    for fname, why in survived:
        print(f"  SURVIVED   {fname}: {why}")
    for fname, why in unviable:
        print(f"  NOT VIABLE {fname}: {why}")
    for fname, why, count in stale:
        print(f"  STALE      {fname}: {why} (old text found {count} times)")
    return 0 if not survived and not stale else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
