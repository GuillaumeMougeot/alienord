# Why does the GPS have no fix?

**Kind:** investigation · **Status:** RESOLVED (2026-10-23): the receiver works, but it sees zero
satellites at its indoor position. It needs sky view; move it to a window.

The heartbeat was three days old, and `gps.txt` repeated `NUll Island. Reinitiating` every 2 s. To
read raw NMEA without fighting the app for the serial port, the app was frozen (`docker pause gps`)
while a throwaway container read it. The output: `$GNRMC,…,V,…` (void), fix quality 0, and
`$GPGSV,1,1,00` (zero satellites in view). The clock and date were correct, so the receiver itself is
fine. It had fixes in the same office on 09-08 and 10-20, and the 2026-10-23 16:18 recording carries
coordinates, so position matters. Without a fix, recordings are named `no_gps` and no detection
images can be saved. Side effect: the message spam made `gps.txt` 354 MB before rotation began.
