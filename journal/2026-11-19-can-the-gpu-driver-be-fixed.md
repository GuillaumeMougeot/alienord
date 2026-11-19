# Can the GPU driver bug be fixed by rebuilding `nvgpu.ko`?

**Kind:** change · **Status:** OPEN: built and verified 11-19; live test next (owner). Owner chose
option 1 (11-19): rebuild NVIDIA's GPU driver module for L4T 35.1 with the fix from 35.2.1
([root cause](2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md#root-cause-a-bug-in-nvidias-gpu-driver-fixed-in-l4t-3521)).
Nothing changed on the unit yet.

## The owner's worry

"If the GPU does not start up again, we are screwed." So, before building anything, we looked at
what a bad module could actually break and how it would be undone.

## What we found before building (read-only, 11-19)

- **The running kernel is Lenovo's own build** (22 Sep 2023, built from
  `.../lenovo/kernel-src/...`, compiler Buildroot gcc 9.3), not NVIDIA's 2022 package, although
  `dpkg` lists NVIDIA's `nvidia-l4t-kernel 35.1.0`. Lenovo built `nvgpu.ko` the same day from their
  copy of NVIDIA's source; whether they changed it is unknown.
- **The installed kernel headers do not match it.** Of the 388 kernel symbols `nvgpu.ko` imports,
  156 have a different version checksum in the headers' `Module.symvers`, including
  `module_layout`. A module built naively against these headers would be refused at load time
  ("disagrees about version of symbol"): harmless, but useless.
- **Why:** `/proc/config.gz` differs from the headers' `.config` in 22 lines. The one that matters
  is module signing (`CONFIG_MODULE_SIG`: off in the running kernel, on in the headers), which
  changes `struct module`; every symbol whose types reach it gets a different checksum. No struct
  layout randomisation (`GCC_PLUGIN_RANDSTRUCT` off); no module signature enforcement.
- **How nvgpu loads:** from the root filesystem on the NVMe (`/etc/modules-load.d/nv.conf`), not
  from the initrd. It can be unloaded (`MODULE_UNLOAD=y`, the module has an exit function).
- **Boot:** root is the NVMe (`nvme0n1p1`); the boot menu (`extlinux.conf`, `TIMEOUT 10`, which in
  this format is probably tenths of a second, so ~1 s: too short to use; to be lengthened) appears
  to be read from the eMMC system (`mmcblk0p1`, not mounted), because the running command line
  does not match the NVMe copy of `extlinux.conf`. To be confirmed by root before relying on it.
- The owner works at the unit (desktop `:1` plus tmux), so screen and keyboard are available for
  the boot menu.

## Risk, and how the plan contains it

| what goes wrong | effect | undo |
|---|---|---|
| module refused (checksums, symbols) | no GPU: no recording, maybe no desktop; the unit boots, network works | nothing persistent if it happens during the test; after install, delete one file + reboot |
| module loads but crashes | kernel oops/panic | during the test: reboot brings the original back. After install: a pre-made boot-menu entry with `module_blacklist=nvgpu`, then delete the file |
| module works but misbehaves | wrong clocks, errors | the guard keeps running; delete the file + reboot |
| crashes every boot **and** the boot menu fails | the real "screwed" case | take out the NVMe and fix it on another Linux PC; or a Lenovo reflash |

The plan never overwrites the original file and runs the new module live before it is ever
loaded at boot:

1. **Build (agent, no root, changes nothing):** NVIDIA's `jetson_35.1` nvgpu source; build tree
   from the headers with the *running* kernel's config; checksums taken from the modules Lenovo
   built. Check: an *unmodified* build must match Lenovo's module (symbols, strings) before the
   patch is applied, and `module_layout`'s checksum recomputed from the kernel source must equal the
   running kernel's. `nice`, two jobs, power watched.
2. **Live test (owner, sudo script):** stop recording and the desktop, unload `nvgpu`, load the
   new one, check recording, the decoder probe and Firefox. A crash here costs a reboot.
3. **Install (owner):** into `/lib/modules/5.10.104-tegra/updates/` (the original stays in
   `kernel/`), plus the boot-menu fallback entry; reboot and check.
4. Keep the guard: once the fix is in, it should never act again.

## How to revert, case by case (written before building, 11-19)

The maintained version, readable from another device: [docs/gpu-driver-fix.md](../docs/gpu-driver-fix.md).

The files involved:

| file | what |
|---|---|
| `/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko` | **original** (Lenovo), never modified. sha256 `b62d7dec1c2b91804c909a2c18251488e83b009db88369b2e9fa4573bbc13f67` |
| `/lib/modules/5.10.104-tegra/updates/nvgpu.ko` | the **fixed** copy; this folder does not exist yet and is created only at install (step 3) |
| `/lib/modules/5.10.104-tegra/modules.dep` | the module index, rebuilt by `depmod`; after install it points `nvgpu` at `updates/` |

Because the index points at `updates/nvgpu.ko` after the install, **the one-command revert copies
the original over the fixed copy**; it works without re-running `depmod`:

```
sudo cp /lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko /lib/modules/5.10.104-tegra/updates/nvgpu.ko && sync && sudo reboot
```

The tidy version (removes the folder entry and rebuilds the index; both steps are needed, deleting
alone leaves the index pointing at a missing file and no GPU):
`sudo rm /lib/modules/5.10.104-tegra/updates/nvgpu.ko && sudo depmod -a 5.10.104-tegra && sudo reboot`.
Check afterwards: `modinfo -n nvgpu` shows the `kernel/...` path and `sha256sum` matches the above.

| case | what you do |
|---|---|
| live test: new module refused | `sudo modprobe nvgpu` reloads the original, then restart the desktop and recording; or just reboot. Nothing was written to disk. |
| live test: freeze or crash | reboot (hold the power button if frozen). Nothing was written to disk, so the original loads. |
| installed: works but misbehaves | the one-command revert above, at any time. |
| installed: refused at boot (no GPU, no desktop) | text console (Ctrl+Alt+F3) or SSH, log in, the one-command revert. |
| installed: crashes at every boot | at power-on, pick the boot-menu entry **"no GPU driver"** (same system plus `module_blacklist=nvgpu`, added at install, with the menu wait lengthened). It boots without the GPU driver: console, one-command revert, reboot normally. |
| that menu does not work either | take the NVMe out, put it in a USB enclosure on any Linux PC, mount its partition and copy `<mnt>/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko` over `<mnt>/lib/modules/5.10.104-tegra/updates/nvgpu.ko`; put it back. Possibly also a boot entry for the eMMC system (to check at install). Last resort: Lenovo reflash. |

The install script will also place this revert as a root-owned script on the unit, so it is one
short command to type from a console.

## The build (11-19, morning)

Details, inputs and tools: [`tools/nvgpu-fix/`](../tools/nvgpu-fix/README.md). What happened, in order:

1. **The fix is bigger than we said.** We had called it "about 10 lines". NVIDIA's 35.2.1 change
   is 249 lines in 11 files: 35.1 had PM QoS support switched off (`CONFIG_GK20A_PM_QOS := n`), so
   the driver never learned the power-mode cap at all; 35.2.1 switches it on, adds min/max
   frequency notifiers for kernel 5.10, and only then clamps the arbiter. We kept exactly those
   hunks and left out the rest of 35.2.1.
2. `make` is not installed; Ubuntu's package was downloaded through apt and unpacked locally (no
   root, nothing installed).
3. Kconfig cannot run in the headers-only tree, so the two generated config files were written by
   a small script, validated by reproducing NVIDIA's own files exactly.
4. The checksum mismatch was solved by reading the CRC table **out of the running kernel image**
   (`/boot/Image`), cross-checked against the 1,095 modules Lenovo built: 5,018 agree, 0 disagree.
   Compiling the kernel's own `module.c` and `qos.c` in our tree reproduced the image's values
   (`module_layout 0xc23f4489`, `dev_pm_qos_add_notifier 0xb64e7201`), so our build sees the same
   kernel structures as Lenovo's.
5. **Caught before it mattered:** the fix needs two kernel functions no Lenovo module uses
   (`dev_pm_qos_add/remove_notifier`). Their checksums in NVIDIA's headers were wrong for this
   kernel; the first fixed build carried them and would have been **refused at load** (harmless,
   but the test would have failed). The kernel image gave the right values; relinked.
6. One NVIDIA header missing from the headers package (`nvmap_exports.h`, three declarations) was
   taken from the 35.1 source mirror; its only commit there is NVIDIA's import.
7. **Unmodified build = Lenovo's module** in everything but compiler output: same imports and
   checksums, same symbols, same data sizes, same strings. Lenovo did not change NVIDIA's driver.
8. Fixed module: `nvgpu-fixed.ko`, sha256 `761608e8…f3ec`; all 390 imports verified.

Power while building (2 jobs, lowest priority): 14.4 W average, 15.2 W peak.

## Live test, first attempt (11-19, 14:07): interrupted, driver untouched

The owner ran the script from a text console (tty3). It stopped the guard, recording and the
camera daemon, then the desktop, and was killed at 14:07:07, before its next step: gdm's unit has
`ExecStopPost=/bin/loginctl terminate-seat seat0`, so stopping gdm logs out **every** session on
the unit's screen and keyboard, text consoles included (`Stopped Session 513 of user xnx`,
`getty@tty3` restarted). Our runbook's "use a text console" advice did not protect against that:
our mistake. The original driver was never unloaded (still loaded, nothing using it). The owner
was left with a black screen on Ctrl+Alt+F1 and all services stopped; restored with
`/tmp/gpu-test-restore.sh`. The script now re-launches itself under `systemd-run`, outside any
login session, and the owner follows the log.

A detail for the live test: a freshly loaded driver creates a new frequency device whose cap is
"no limit"; the test re-runs the boot-time power-mode command (`nvpmodel -f /etc/nvpmodel.conf`)
right after loading, before anything uses the GPU, which also sets mode 5's TPC power-gating mask.
