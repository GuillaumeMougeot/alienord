# Can the GPU driver bug be fixed by rebuilding `nvgpu.ko`?

**Kind:** change · **Status:** OPEN. Owner chose option 1 (11-19): rebuild NVIDIA's GPU driver module
for L4T 35.1 with the ~10-line fix from 35.2.1
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
- **Boot:** root is the NVMe (`nvme0n1p1`); the boot menu (`extlinux.conf`, 10 s timeout) appears
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
