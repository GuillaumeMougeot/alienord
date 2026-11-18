# Why does the unit reset?

**Kind:** incident · **Status:** OPEN (watching). Every unexplained reset is the module's power cutting out.
**Update 2026-11-18: the sustained load behind the two logged cut-outs was a GPU clock stuck at
maximum, now guarded against**; see the updates at the end. Next: watch for any further reset.

## The evidence: the power chip's event recorder

At each boot the kernel prints why the board last lost power:
`max77620-power max20024-power: Event recorder REG_NVERC : 0x..`. Bit 6 = input undervoltage lockout,
bit 4 = input low, bit 2 = hard reset. Every boot through the external reset line (`SYS_RESET_N`) on
record, since March 2025, shows `0x54` or `0x44`, both of which include input undervoltage. Every
software reboot (`MAINSWRST`) shows `0x0`. No panic, thermal or over-current messages. `last -x`
reports `crash`.

## Every reset on record since the investigation began

| Reset (local) | Button pressed just before? | Note |
|---|---|---|
| 2026-10-23 13:28 | **yes**, 13:27:57 | recording destroyed |
| 2026-10-23 14:19 | **yes**, 14:19:16 | recording destroyed |
| 2026-10-23 15:28 | no | nobody touched the unit (owner) |
| 2026-10-23 16:19 | **yes**, 16:18:56 | found 2026-11-17 from its files; the journal had lost the press |
| 2026-10-23 16:32 | no | |
| 2026-10-23 16:44, 10-26 17:11 | no | possibly deliberate power-offs |

On 2026-09-08, by contrast, seven presses caused no reset. So **every press since September has
reset the unit**, and the power path also fails without one.

## What has been ruled out

- **Software**, **heat** (SoC 50-56 °C) and **power-mode changes** (`se70_thread` only switches
  `nvpmodel`, which never changed).
- **An overloaded supply, probably.** On 2026-11-16 the unit ran 3.5 h at a load average above 30
  while downloading 460 GB. The input rail never dropped below 4.936 V (peak 3.2 A) and there was no
  reset. A weak supply should have sagged under that load.

Holding the button cannot matter in software: the script starts one recording and ignores the button
for 5 s. So the trigger is electrical or mechanical: the button wiring, or force on a loose connector.

## The input-power logger

`vd-power-log.service` (installed 2026-11-16) writes the module's 5 V input twice a second to
`/var/log/vd-power/`, flushed every line. After the next collapse, its last lines show whether the
rail sagged first or stayed steady to the end (an abrupt cut). Caveat: it measures after the carrier
board's regulator, so measuring the box's DC input directly is the definitive test.

## Next tests, in order

1. **Software trigger, no button** (`kill -USR1`, see [`../docs/operations.md`](../docs/operations.md#recording-with-the-button)).
   It ran fine on 2026-09-08. If the unit survives, the recording load is cleared.
2. **One short tap on the button**, with the power logger running. A reset confirms the button
   path; the logger shows whether the rail sagged.
3. **Open the button box:** check what the button and LED are wired to, and whether either shares the
   supply or the SE70's power or reset inputs. Then every connector on the power feed.

Before each test: `sync`, and nothing important being written. Each reset forces an ext4 recovery.

## Update 2026-11-17: a reset with no press, caught by the power logger

1. **A short press does not reset the unit.** The owner tapped the button at 09:10:40: a normal
   recording, no reset, input rail steady at 4.952 V.
2. **At 09:54:53 the unit reset with no press**, and the logger caught it. At 09:15:50 Firefox had
   been started on the unit's desktop (`/usr/lib/firefox/firefox -new-window`). Its graphics
   acceleration fails here (`NvRmMemInit failed`), so it renders and decodes on the CPU. The module's
   draw jumped within three seconds from ~2.3 A to **~3.85 A** (~12 W to ~19 W), CPU+GPU from 1.1 A
   to 2.4 A, and stayed there for 40 min, peaking at 4.32 A. The last samples read 3.83 → 4.16 A
   with **the voltage flat at 4.920-4.928 V up to the last one** (09:54:53.587), then nothing. The
   power chip recorded input undervoltage (`0x54`), as before.
3. **What that means.** The 5 V rail did not sag: whatever feeds it **cut out abruptly**, after 40
   minutes at a load ~60 % above normal. The 3.5 h download (peak 3.2 A) survived; a quiet press at
   2.5 A survived. The likely culprit is a power supply working near its limit and tripping its
   protection (current or heat) under sustained load. On 2026-10-23 the unit was often busy with
   diagnostic work when a press added a burst of load on top: docker commands, a JPEG burst, and a
   second recording if the button is held past 5 s. That would explain the press correlation
   without any wiring fault. **This replaces the "button wiring" conclusion above, which was ours
   and premature.**

**Next:**
1. Identify the unit's power supply (label: volts, amps or watts) and what else it feeds; the
   cameras, switch and 4G router may share it.
2. Try a higher-rated supply; the logger shows the difference.
3. Until then, keep the unit's load low: **no web browser or other heavy desktop app on the
   Jetson.** Browse from another computer.
4. Optional: run without the desktop (`sudo systemctl set-default multi-user.target`), and/or cap
   the power mode with `nvpmodel` (it is in mode 5, `MODE_10W_DESKTOP`, yet drew ~19 W at the input).

**2026-11-17, later:** the owner held the button for a **longer** press, at normal load: no reset.
Together with the short press, the button is cleared on its own. The owner confirms that ~19 W is at
the limit of the power supply they bought. In normal use (no browser on the unit) the load is
~12-15 W, so this should not happen in the field. Still worth a supply with headroom, for summer heat
in a vehicle.

**2026-11-18: a second load-caused reset, from video playback.** The owner played one of the
Swedish 4K recordings on the unit's desktop. At 10:13:15 the module's draw rose from ~2.3 A to
**~3.94 A** (~19.4 W; CPU+GPU 1.1 → 2.43 A); at 11:23:55 the power cut, after **70 minutes**, voltage
flat at 4928 mV to the last sample, `0x54` again. Temperatures moderate (CPU 64 °C, GPU 69 °C). Two
cuts at the same load, after 40 and 70 minutes, point to the supply's own protection tripping once it
has heated up at its rated limit (~19 W, owner), not an instant overload. **Rule: no browser and no
video playback on the unit**; copy videos to another computer.

**2026-11-18, evening: the extra 8 W was a stuck GPU clock, not the apps.** Starting Firefox and
closing a video player that used the hardware decoder both leave the GPU clock at 1109 MHz, above the
power mode's 510 MHz cap, until reboot; at the recording pipeline's 99 % GPU load that is the whole
jump from ~2.3 A to ~3.94 A. Both 11-17 and 11-18 match: the 11-17 step came 5 s after Firefox
started; on 11-18 Totem had been closed after 12 s. `gpu-clock-guard.service` now resets the clock
within ~10 s. Full account: [2026-11-18](2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md).
The "no browser, no video" rule above is lifted while the guard runs. Still open: whether any reset
happens with the guard in place; earlier resets (before the logger) cannot be checked.
