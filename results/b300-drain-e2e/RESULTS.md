# B300 drain/occupancy/e2e/toolkit session (2026-07-07T01:14:58Z, rev ba16fad7f, clocks locked)

## 1. Drain ablation throughput (min-of-100, locked clocks)

| cell | kernel | decode_ms(min) | GiB/s | verified |
|---|---|---|---|---|
| clickbench/URL b12 | onpair_shmem | 1.6503 | 564.3 | True |
| clickbench/URL b12 | onpair_shmem_4tpt | 1.3174 | 706.9 | True |
| clickbench/URL b12 | onpair_shmem_4tpt_ablate | 1.2130 | 767.8 | True |
| clickbench/URL b12 | onpair_shmem_4tpt_ablate_nodrain | 1.0865 | 857.2 | False |
| clickbench/URL b12 | (auto=onpair_shmem_4tpt_split8read_b128o12, best=onpair_shmem_4tpt_split8read_b128o12) | | 841.9054734361581 | |
| clickbench/URL b12 | DRAIN COST vs _ablate baseline | +0.1264 ms | 10.4% of ablate | |
| clickbench/URL b12 | DRAIN COST vs plain 4tpt | +0.2309 ms | 17.5% of 4tpt | |
| tpch-sf10/l_shipinstruct b12 | onpair_shmem | 0.6328 | 1059.4 | True |
| tpch-sf10/l_shipinstruct b12 | onpair_shmem_4tpt | 0.5204 | 1288.2 | True |
| tpch-sf10/l_shipinstruct b12 | onpair_shmem_4tpt_ablate | 0.4663 | 1437.5 | True |
| tpch-sf10/l_shipinstruct b12 | onpair_shmem_4tpt_ablate_nodrain | 0.4137 | 1620.5 | False |
| tpch-sf10/l_shipinstruct b12 | (auto=onpair_shmem_4tpt_b128o12, best=onpair_shmem_4tpt_vwidth4_b128) | | 1468.8404357091351 | |
| tpch-sf10/l_shipinstruct b12 | DRAIN COST vs _ablate baseline | +0.0527 ms | 11.3% of ablate | |
| tpch-sf10/l_shipinstruct b12 | DRAIN COST vs plain 4tpt | +0.1067 ms | 20.5% of 4tpt | |
| tpch-sf10/ps_comment b12 | onpair_shmem | 0.8752 | 1051.3 | True |
| tpch-sf10/ps_comment b12 | onpair_shmem_4tpt | 0.7840 | 1173.5 | True |
| tpch-sf10/ps_comment b12 | onpair_shmem_4tpt_ablate | 0.7231 | 1272.4 | True |
| tpch-sf10/ps_comment b12 | onpair_shmem_4tpt_ablate_nodrain | 0.6279 | 1465.3 | False |
| tpch-sf10/ps_comment b12 | (auto=onpair_shmem_4tpt_b128o12, best=onpair_shmem_4tpt_b512o3) | | 1277.4988017146547 | |
| tpch-sf10/ps_comment b12 | DRAIN COST vs _ablate baseline | +0.0952 ms | 13.2% of ablate | |
| tpch-sf10/ps_comment b12 | DRAIN COST vs plain 4tpt | +0.1561 ms | 19.9% of 4tpt | |
| tpch-sf10/ps_comment b16 | onpair_shmem | 0.9716 | 947.0 | True |
| tpch-sf10/ps_comment b16 | onpair_shmem_4tpt | 0.9770 | 941.8 | True |
| tpch-sf10/ps_comment b16 | onpair_shmem_4tpt_ablate | 0.8830 | 1042.0 | True |
| tpch-sf10/ps_comment b16 | onpair_shmem_4tpt_ablate_nodrain | 0.7859 | 1170.7 | False |
| tpch-sf10/ps_comment b16 | (auto=onpair_shmem_4tpt_b128o12, best=onpair_shmem_4tpt_b64) | | 1049.329058435522 | |
| tpch-sf10/ps_comment b16 | DRAIN COST vs _ablate baseline | +0.0971 ms | 11.0% of ablate | |
| tpch-sf10/ps_comment b16 | DRAIN COST vs plain 4tpt | +0.1910 ms | 19.6% of 4tpt | |
| synthetic/url b12 | onpair_shmem | 0.7301 | 1178.1 | True |
| synthetic/url b12 | onpair_shmem_4tpt | 0.6454 | 1332.6 | True |
| synthetic/url b12 | onpair_shmem_4tpt_ablate | 0.5962 | 1442.8 | True |
| synthetic/url b12 | onpair_shmem_4tpt_ablate_nodrain | 0.5285 | 1627.5 | False |
| synthetic/url b12 | (auto=onpair_shmem_4tpt_b128o12, best=onpair_shmem_4tpt_b512o3) | | 1439.634026698363 | |
| synthetic/url b12 | DRAIN COST vs _ablate baseline | +0.0676 ms | 11.3% of ablate | |
| synthetic/url b12 | DRAIN COST vs plain 4tpt | +0.1169 ms | 18.1% of 4tpt | |

## 2. NCU captures (--set full, -c 16, exact -k, 30-iter gpu-decode-vortex)

### NCU clickbench/URL b12 -k onpair_shmem_4tpt_ablate_nodrain (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem_4tpt_ablate_nodrain'] shared_max=8.32
  Achieved Active Warps Per SM [warp]: mean=40.8813 over 16 launches
  Achieved Occupancy [%]: mean=63.8769 over 16 launches
  Block Size []: mean=128.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=58.9763 over 16 launches
  DRAM Throughput [%]: mean=3.8931 over 16 launches
  Duration [ms]: mean=1.8106 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=1986667.5625 over 16 launches
  Grid Size []: mean=416151.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.5200 over 16 launches
  L1/TEX Cache Throughput [%]: mean=98.0781 over 16 launches
  L2 Cache Throughput [%]: mean=4.1588 over 16 launches
  Memory Throughput [%]: mean=97.8625 over 16 launches
  Memory Throughput [Gbyte/s]: mean=298.7131 over 16 launches
  Registers Per Thread [register/thread]: mean=40.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=8.3200 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=48.0000 over 16 launches
  Theoretical Occupancy [%]: mean=75.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=19.7481 over 16 launches

### NCU tpch-sf10/ps_comment b16 -k onpair_shmem_4tpt_ablate_nodrain (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem_4tpt_ablate_nodrain'] shared_max=8.32
  Achieved Active Warps Per SM [warp]: mean=42.8219 over 16 launches
  Achieved Occupancy [%]: mean=66.9100 over 16 launches
  Block Size []: mean=128.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=28.7594 over 16 launches
  DRAM Throughput [%]: mean=1.8812 over 16 launches
  Duration [ms]: mean=1.3513 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=1483190.4375 over 16 launches
  Grid Size []: mean=151408.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.2500 over 16 launches
  L1/TEX Cache Throughput [%]: mean=99.4750 over 16 launches
  L2 Cache Throughput [%]: mean=28.6750 over 16 launches
  Memory Throughput [%]: mean=99.0687 over 16 launches
  Memory Throughput [Gbyte/s]: mean=144.4131 over 16 launches
  Registers Per Thread [register/thread]: mean=40.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=8.3200 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=48.0000 over 16 launches
  Theoretical Occupancy [%]: mean=75.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=42.3719 over 16 launches

### NCU clickbench/URL b12 -k onpair_shmem (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem'] shared_max=8.7
  Achieved Active Warps Per SM [warp]: mean=57.1569 over 16 launches
  Achieved Occupancy [%]: mean=89.3081 over 16 launches
  Block Size []: mean=512.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=71.0487 over 16 launches
  DRAM Throughput [%]: mean=7.2231 over 16 launches
  Duration [ms]: mean=2.5700 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=2813257.6250 over 16 launches
  Grid Size []: mean=416151.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.7100 over 16 launches
  L1/TEX Cache Throughput [%]: mean=84.5950 over 16 launches
  L2 Cache Throughput [%]: mean=9.5813 over 16 launches
  Memory Throughput [%]: mean=84.4594 over 16 launches
  Memory Throughput [Gbyte/s]: mean=554.1831 over 16 launches
  Registers Per Thread [register/thread]: mean=32.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=8.7000 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=64.0000 over 16 launches
  Theoretical Occupancy [%]: mean=100.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=19.9750 over 16 launches

### NCU clickbench/URL b12 -k onpair_shmem_4tpt (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem_4tpt'] shared_max=33.28
  Achieved Active Warps Per SM [warp]: mean=29.0712 over 16 launches
  Achieved Occupancy [%]: mean=45.4225 over 16 launches
  Block Size []: mean=512.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=52.5550 over 16 launches
  DRAM Throughput [%]: mean=8.3287 over 16 launches
  Duration [ms]: mean=2.1606 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=2368283.6250 over 16 launches
  Grid Size []: mean=104038.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.5100 over 16 launches
  L1/TEX Cache Throughput [%]: mean=92.2731 over 16 launches
  L2 Cache Throughput [%]: mean=9.3262 over 16 launches
  Memory Throughput [%]: mean=92.0419 over 16 launches
  Memory Throughput [Gbyte/s]: mean=638.8744 over 16 launches
  Registers Per Thread [register/thread]: mean=56.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=33.2800 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=32.0000 over 16 launches
  Theoretical Occupancy [%]: mean=50.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=14.1613 over 16 launches

### NCU dbtext/ps_comment b12 -k onpair_shmem_4tpt_b128o12 (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem_4tpt_b128o12'] shared_max=8.32
  Achieved Active Warps Per SM [warp]: mean=12.3925 over 16 launches
  Achieved Occupancy [%]: mean=19.3656 over 16 launches
  Block Size []: mean=128.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=13.6306 over 16 launches
  DRAM Throughput [%]: mean=0.7938 over 16 launches
  Duration [us]: mean=9.6781 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=10520.1875 over 16 launches
  Grid Size []: mean=492.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.2444 over 16 launches
  L1/TEX Cache Throughput [%]: mean=65.4450 over 16 launches
  L2 Cache Throughput [%]: mean=7.8519 over 16 launches
  Memory Throughput [%]: mean=36.3975 over 16 launches
  Memory Throughput [Gbyte/s]: mean=60.5969 over 16 launches
  Registers Per Thread [register/thread]: mean=40.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=8.3200 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=48.0000 over 16 launches
  Theoretical Occupancy [%]: mean=75.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=12.8981 over 16 launches

### NCU dbtext/ps_comment b12 -k onpair_shmem_4tpt (ncu exit=0)
CAPTURE-VERIFIED kernels=['onpair_shmem_4tpt'] shared_max=33.28
  Achieved Active Warps Per SM [warp]: mean=15.1569 over 16 launches
  Achieved Occupancy [%]: mean=23.6825 over 16 launches
  Block Size []: mean=512.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=13.6800 over 16 launches
  DRAM Throughput [%]: mean=0.7769 over 16 launches
  Duration [us]: mean=9.8919 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=10746.1250 over 16 launches
  Grid Size []: mean=123.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.2581 over 16 launches
  L1/TEX Cache Throughput [%]: mean=68.8425 over 16 launches
  L2 Cache Throughput [%]: mean=7.4787 over 16 launches
  Memory Throughput [%]: mean=36.0450 over 16 launches
  Memory Throughput [Gbyte/s]: mean=59.2844 over 16 launches
  Registers Per Thread [register/thread]: mean=56.0000 over 16 launches
  Static Shared Memory Per Block [Kbyte/block]: mean=33.2800 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=32.0000 over 16 launches
  Theoretical Occupancy [%]: mean=50.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=14.9175 over 16 launches

## 3. E2E scan (ClickBench URL b12 dump, repro-repo e2e_scan.cu)

### e2e baseline (nvcc 13.0 native, 100 iters) exit=0
```json
{
  "gpu": "NVIDIA B300 SXM6 AC",
  "sm": "10.3",
  "kernel": "onpair_shmem_4tpt_split8read",
  "total_tokens": 213069107,
  "dict_size": 4096,
  "decoded_bytes": 999999995,
  "compressed_bytes": 426163850,
  "ratio": 2.3465,
  "iters": 100,
  "needle_hex": "db8c20d987d8a7db8c687474702533412f2f6d6173746572",
  "needle_len": 24,
  "decode_ok": true,
  "scan_ok": true,
  "cpu_matches": 1,
  "gpu_matches": 1,
  "decode_ms": 1.29622,
  "scan_ms": 0.21987,
  "e2e_ms": 1.51834,
  "h2d_decompressed_ms": 17.97984,
  "h2d_compressed_ms": 7.66275,
  "cpu_decode_ms": 555.58577,
  "decode_gbps": 771.47,
  "scan_gbps": 4548.10,
  "e2e_gbps": 658.62,
  "h2d_decompressed_gbps": 55.62,
  "h2d_compressed_gbps": 55.61,
  "cpu_decode_gbps": 1.80,
  "e2e_overhead_pct": 17.14,
  "gpu_native_total_ms": 9.17885,
  "cpu_decode_pcie_scan_total_ms": 573.78548,
  "pcie_decompressed_vs_gpu_decode_scan": 11.86
}
```

### NCU e2e scan_needle (ncu exit=0)
CAPTURE-VERIFIED kernels=['scan_needle(const unsigned char *, unsigned long, const unsigned char *, unsigned int, unsigned char, unsigned int, unsigned long long *)'] shared_max=0.0
  Achieved Active Warps Per SM [warp]: mean=50.3612 over 16 launches
  Achieved Occupancy [%]: mean=78.6863 over 16 launches
  Block Size []: mean=256.0000 over 16 launches
  Compute (SM) Throughput [%]: mean=64.4631 over 16 launches
  DRAM Throughput [%]: mean=42.7500 over 16 launches
  Duration [us]: mean=305.9762 over 16 launches
  Dynamic Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Elapsed Cycles [cycle]: mean=335013.0625 over 16 launches
  Grid Size []: mean=244141.0000 over 16 launches
  Issued Warp Per Scheduler []: mean=0.6500 over 16 launches
  L1/TEX Cache Throughput [%]: mean=20.9806 over 16 launches
  L2 Cache Throughput [%]: mean=35.4394 over 16 launches
  Memory Throughput [%]: mean=42.7500 over 16 launches
  Memory Throughput [Tbyte/s]: mean=3.2794 over 16 launches
  Registers Per Thread [register/thread]: mean=30.0000 over 16 launches
  Static Shared Memory Per Block [byte/block]: mean=0.0000 over 16 launches
  Theoretical Active Warps per SM [warp]: mean=64.0000 over 16 launches
  Theoretical Occupancy [%]: mean=100.0000 over 16 launches
  Warp Cycles Per Issued Instruction [cycle]: mean=19.0081 over 16 launches

## 4. Toolkit check (nvcc 12.8 vs 13.0)

### onpair_shmem_4tpt
- PTX nvcc12.8 vs nvcc13.0 @compute_100: DIFFERS (1194 diff lines)
- SASS via fixed ptxas13.0 @sm_103 (driver-JIT analogue), 12.8-PTX vs 13.0-native-PTX: DIFFERS (1038 diff lines)
- SASS per-toolkit ptxas @sm_100 (classic AOT): DIFFERS (1038 diff lines)

### onpair_shmem_4tpt_split8read
- PTX nvcc12.8 vs nvcc13.0 @compute_100: DIFFERS (1342 diff lines)
- SASS via fixed ptxas13.0 @sm_103 (driver-JIT analogue), 12.8-PTX vs 13.0-native-PTX: DIFFERS (1086 diff lines)
- SASS per-toolkit ptxas @sm_100 (classic AOT): DIFFERS (1086 diff lines)

- timing 128_sm100: exit=0 decode_ms=1.3137 decode_gbps=761.21 scan_gbps=4771.72 e2e_gbps=655.23 decode_ok=True scan_ok=True
- timing 130_sm100: exit=0 decode_ms=1.29581 decode_gbps=771.72 scan_gbps=4574.73 e2e_gbps=658.66 decode_ok=True scan_ok=True
- timing 130_sm100_cubinonly: exit=0 decode_ms=1.2961 decode_gbps=771.55 scan_gbps=4559.38 e2e_gbps=658.62 decode_ok=True scan_ok=True
- timing 130native: exit=0 decode_ms=1.29622 decode_gbps=771.47 scan_gbps=4546.12 e2e_gbps=658.62 decode_ok=True scan_ok=True

