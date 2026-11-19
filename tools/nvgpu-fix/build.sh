#!/bin/bash
# build.sh <source tree>  -- builds nvgpu.ko out of tree against the Lenovo-matched header tree
set -o pipefail
B=/home/xnx/build/nvgpu-fix; T=$(readlink -f "$1")
export PATH=$B/tools/root/usr/bin:$PATH
nice -n 19 make -C $B/kh/kernel-5.10 M=$T/drivers/gpu/nvgpu srctree.nvgpu=$T srctree.nvidia=$B/kh/nvidia -j2 modules > $T/build.log 2>&1
echo "exit $?" >> $T/build.log; sync
