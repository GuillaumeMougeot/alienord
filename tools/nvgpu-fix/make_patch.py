# Build the backport patch: NVIDIA's own 35.1 -> 35.2.1 changes for the clock-arbiter/PM-QoS fix only.
import subprocess, re, sys
O = 'a'; N = 'b'
whole = ['os/linux/scale.c', 'os/linux/scale.h', 'common/clk_arb/clk_arb_gp10b.c', 'common/clk_arb/clk_arb_gv100.c',
         'os/linux/vgpu/vgpu_linux.c', 'os/linux/platform_gv11b_tegra.c', 'os/linux/platform_gk20a_tegra.c']
partial = {'os/linux/platform_gk20a.h': r'qos_|linux/version\.h', 'os/linux/driver_common.c': r'qos_|linux/version\.h',
           'os/linux/platform_ga10b_tegra.c': r'qos_', 'Makefile.linux.configs': r'(?m)^\+CONFIG_GK20A_PM_QOS := y'}
out = []
for f in whole + list(partial):
    d = subprocess.run(['diff', '-u', '--label', f'a/drivers/gpu/nvgpu/{f}', '--label', f'b/drivers/gpu/nvgpu/{f}',
                        f'src/linux-nvgpu-jetson_35.1/drivers/gpu/nvgpu/{f}', f'ref/linux-nvgpu-jetson_35.2.1/drivers/gpu/nvgpu/{f}'],
                       capture_output=True, text=True).stdout
    head, *hunks = re.split(r'(?m)^(?=@@ )', d)
    if f in partial:
        keep = [h for h in hunks if re.search(partial[f], ''.join(l for l in h.splitlines(True) if l[:1] in '+-'))]
    else:
        keep = hunks
    print(f, 'hunks', len(hunks), 'kept', len(keep), file=sys.stderr)
    out.append(head + ''.join(keep))
open('patch/nvgpu-35.1-clk-arb-qos-backport.patch', 'w').write(''.join(out))
