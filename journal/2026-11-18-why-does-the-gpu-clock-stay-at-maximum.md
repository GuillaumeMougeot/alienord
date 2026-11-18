# Why does the power stay high after the video player is closed?

**Kind:** incident · **Status:** RESOLVED. Using the hardware video decoder, or starting Firefox,
leaves the **GPU clock at its maximum (1109 MHz) instead of the power mode's 510 MHz cap**, which
adds ~8 W until reboot. That was the "high load" behind both supply cut-outs (11-17, 11-18). A guard
service now pulls the clock back within ~10 s: `gpu-clock-guard.service`.

## The question

The owner (11-18): the morning's crash came long after the video was opened, and *"how come it does
not go down as soon as the media player is closed? could you fix that?"*

## What the morning looked like

Totem was started from the file manager at 10:13:08 and its settings file was written at 10:13:20,
so it was closed after ~12 s. The module's draw rose at 10:13:15 from ~2.3 A to ~3.94 A and stayed
there, flat, until the power cut at 11:23:55. The video is 13.5 min long, so even playing to the end
would not explain 70 min. Something outlived the player.

## Reproducing it (by accident first)

At 16:30:53 we ran `gst-discoverer-1.0` on the same file to read its length: a one-second metadata
probe. The draw jumped from ~2.5 A to ~3.95 A at that second and stayed there, with no process using
noticeable CPU. `tegrastats` showed GR3D at 99 % and
`/sys/devices/17000000.gv11b/devfreq/17000000.gv11b/` showed:

| | normal | stuck |
|---|---|---|
| `cur_freq` | 510 MHz | **1109 MHz** |
| `target_freq` (what the governor wants) | 510 MHz | 510 MHz |
| `max_freq` (cap from power mode 5, `MODE_10W_DESKTOP`) | 510 MHz | 510 MHz |

The kernel logged NVDEC firmware loading at that moment: the probe had picked NVIDIA's hardware
decoder `nvv4l2decoder`. A deliberate repeat at 16:43:07 confirmed it: the clock jumps to 1109 MHz as
the decoder is torn down, and stays.

Normally the GPU sits at the 510 MHz cap and 99 % busy: the recording pipeline is GPU-bound. At
1109 MHz it is just as busy and burns ~8 W more, putting the unit at ~19.4 W, the supply's limit.

## Dead ends

1. **Who holds it?** As root (owner): only `nvargus-daemon`, the two `Xorg`, the two `gnome-shell`
   and the deepstream app had the GPU's control node open. NVIDIA's power-hint daemon `nvphsd` is
   in "Zombie mode" (fails at start-up on this unit), so not it.
2. **Four standard resets did nothing** (`/tmp/gpu-reset-test.sh`, run by the owner at 16:44):
   re-writing `max_freq`, cycling the governor, re-applying `nvpmodel -m 5`, restarting
   `nvargus-daemon`. The owner rebooted.
3. **"Only a reboot clears it": our premature conclusion.** The owner did not accept it ("I cannot
   believe that"), rightly.
4. **Keeping desktop apps off the hardware decoder.** `GST_PLUGIN_FEATURE_RANK` does not exist in
   GStreamer 1.16 (this unit), so the first attempt silently used the hardware decoder again and
   stuck the clock: **our mistake, the third time we triggered it.** A copy of the plugin folder
   without `libgstnvvideo4linux2.so` did work (software decoding), but software decoding of 4K
   HEVC is what pushes the CPU to ~19 W while playing. Removed again once the guard existed.

## What actually works

Root's view (debugfs) while stuck: `gpcclk` at 1109250000 in both the kernel clock tree and the BPMP
firmware, `clk_min_rate` 0, no maximum, `mrq_rate_locked` 0. **No lasting constraint holds the
clock**: it is a stale rate. The clock was set underneath the frequency governor, which still
believes it is at 510 MHz, so asking for 510 MHz again is a no-op. Asking for a *different* value
forces a real change:

```
echo 408000000 > .../max_freq ; echo 510000000 > .../max_freq      # cur_freq: 1109 → 408 → 510 MHz
```

Run by the owner at 16:53 (`/tmp/gpu-reset-test2.sh`, reset "A"): draw 3.93 A → 2.3 A, no reboot.

## The fix: `gpu-clock-guard.service`

`/opt/apps/gpu-clock-guard/gpu_clock_guard.sh`, root, installed by the owner 16:56. Every 5 s it
compares `cur_freq` with `max_freq`; above the cap on two checks in a row, it lowers the cap one step
for a second and restores it, and logs both lines to the journal
(`journalctl -u gpu-clock-guard`). It reads the cap each time, so it follows any `nvpmodel` change.

Tests, with the guard running:

| test | clock | draw | guard |
|---|---|---|---|
| metadata probe (hardware decoder) | 1109 MHz after the probe | 3.9 A | fixed 8 s later |
| Totem playing the 4K video 30 s, hardware decoder | **510 MHz while playing** | **2.8 A** (~13.7 W), Totem ~1 core | |
| …then closing Totem | 1109 MHz at close | 3.9 A | fixed 8 s later |
| starting Firefox (`about:blank`) | 1109 MHz within 2 s | 4.1 A | fixed 6 s later |

At 17:04:33 the owner opened Firefox from the desktop: clock stuck, guard fixed it at 17:04:41-43.
Real use, same result.

So the 11-17 "Firefox" reset was the same thing: the jump came 5 s after Firefox started, during its
graphics start-up, not from browsing. Playing video with the hardware decoder costs ~1 W.

## Does it touch normal operation?

No, by construction. In normal running the governor keeps `cur_freq` at or below `max_freq`
(510 = 510 at the pipeline's load), so the guard only reads two files every 5 s. It acts only when
the clock is *above* the cap, which the governor never causes, and then lowers the cap for about a
second (the pipeline runs at 408 MHz for that second). It never changes the power mode; a later
version (17:07) re-reads and verifies the restored cap, retrying, so a failed write cannot leave the
GPU capped low. A different power mode (`nvpmodel`) or `jetson_clocks` raises the cap or pins the
clock at it, so the guard stays idle there too. In its first hour it acted 4 times: three tests and
one real Firefox start.

## What it changes

- The reset question: the ~19.4 W was this stuck clock, not the apps. With the guard, a browser or a
  video player on the unit is fine again ([operations](../docs/operations.md)).
- Anything that uses the hardware decoder triggers it, including a future pipeline that processes
  video files: keep the guard running.
- The guard is a workaround for a driver bug; the root cause is below.

## Root cause: a bug in NVIDIA's GPU driver, fixed in L4T 35.2.1

The owner rightly asked whether this was a real bug rather than something to work around. A kernel
trace (`/tmp/gpu-trace.sh`, run by the owner 17:2x: `clk_set_rate` events on `gpcclk` with call
stacks, during one probe) caught the single write that sets 1109 MHz:

```
nvgpu_clk_arb_p  clk_set_rate: gpcclk 1109250000
 => clk_set_rate <= nvgpu_linux_clk_set_rate <= gp10b_clk_arb_run_arbiter_cb
 <= nvgpu_clk_arb_worker_poll_wakeup_process_item <= nvgpu_worker_poll_work
```

That is the **clock arbiter** of the GPU driver `nvgpu` (`common/clk_arb/clk_arb_gp10b.c`), not the
frequency governor (`devfreq_monitor` kept reporting 510 MHz throughout). Programs that open the GPU
through NVIDIA's libraries register a clock "session" with the arbiter; when a session comes or goes
(the decoder shutting down, Firefox probing OpenGL) the arbiter re-runs. With no session asking for
a frequency, the L4T 35.1 code falls back to `gpc2clk_default_mhz`, the hardware default (maximum),
clamps it only to the hardware range, and calls `set_rate` directly: **it ignores the power mode's
cap**, and the governor never learns of the change.

NVIDIA's public source (mirror `github.com/OE4T/linux-nvgpu`, tags `jetson_35.*`) shows the fix:
from **`jetson_35.2.1`** on, the arbiter clamps its target with `gk20a_scale_clamp_clk_target()` (the
governor's min/max) and records the rate in `g->last_freq`. `jetson_35.1` lacks both; 35.2.1, 35.3.1,
35.4.1, 35.5 and 35.6.4 have them. This unit runs **L4T 35.1.0** (Lenovo SE70 image
`R35.1.0-0.0.1`, `/etc/se70ota_release`), the first JetPack 5 release.

Real fixes, in order of size:

1. **Rebuild `nvgpu.ko` for 35.1 with that ~10-line backport.** The kernel headers are installed
   (`nvidia-l4t-kernel-headers 35.1.0`). Risk: a bad module means no GPU, so no recording, until
   the original is put back; keep it beside the new one and have console access.
2. **Move to L4T ≥ 35.2.1** (JetPack 5.1): also what DeepStream 6.2 officially requires. On this
   board that has to come from Lenovo's SE70 images, which need checking, and it is a reflash.
3. **Keep the guard** (now): it undoes the same wrong write within ~10 s.
