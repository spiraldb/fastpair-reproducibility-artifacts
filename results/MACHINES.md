# Cloud machines

Every rented cloud instance used to produce the OnPair-GPU results in `results/`.
The local development laptop and the homelab server are deliberately excluded;
this is the cloud fleet only.

Two fleets: the four-GPU decode matrix (the evaluation) and the ten-generation
CPU decode sweep (the cross-stack fixed-stride vs variable-stride comparison
behind `fig:crossstack`). All measurements are decode-only and reproduced from
the archived artifacts; host CPUs are listed for completeness but do not affect
the GPU kernel timings (kernel-only, inputs pre-staged in HBM).

## GPU decode machines

The cross-architecture evaluation matrix, one decode run per GPU. Memory peak is the
vendor-rated bandwidth (HBM, or GDDR6 on the L40S) and matches the paper's architecture
table (`tab:arch`).

| GPU | Architecture | Mem. peak | Device memory | Host CPU | Cloud / region | Driver / CUDA | Date |
|-----|--------------|----------:|---------------|----------|----------------|---------------|------|
| A100-SXM4-40GB | Ampere, sm_80 | 1.56 TB/s | 40 GB HBM2 | AMD EPYC 7J13 (Milan) | Lambda, us-east-1 | 570.148 / 12.8 | 2026-06-05 |
| L40S | Ada Lovelace, sm_89 | 0.86 TB/s | 48 GB GDDR6 | (Lambda host) | Lambda | 12.8-13.0 / 570-580* | 2026-06-26 |
| H100-SXM5 | Hopper, sm_90 | 3.35 TB/s | 80 GB HBM3 | Intel Xeon Platinum 8468 (Sapphire Rapids) | Nebius, eu-north1 | 580.126 / 13.0 | 2026-06-08 |
| B300 SXM6 | Blackwell, sm_103 | 8.0 TB/s | 288 GB HBM3e | Intel Xeon 6776P | Nebius | 580.159 / 13.0 | 2026-06-25 |

\* L40S driver/CUDA was not archived for that leg (see `l40s/run-env.txt`); it falls within
the campaign's CUDA 12.8-13.0 / 570-580 range.

- The **A100** and **L40S** are Lambda runs; the **H100** and **B300** are first-party
  Nebius runs. The NSight Compute cost surface (`--set full`) was captured on all four
  where profiling was unblocked, and the hardware Decompression Engine head-to-head ran
  on the B300.
- **GH200** (a redundant second Hopper) and **B200** (the earlier Blackwell, superseded by
  the B300's complete locked sweep + full NCU) were dropped from the evaluation; their raw
  data is retained in `results/{gh200,b200}`.

## CPU decode-sweep machines

The cross-generational fixed-stride (`fat`) vs variable-stride (`entries`) decode
sweep: ten AWS generations spanning AMD, Intel, and Arm across DDR4 and DDR5.
Every instance is an 8-vCPU `*.2xlarge`, region `us-east-1`, with decode pinned
to physical cores (1/2/4-core runs over a 256 MB working set).

Memory is the socket's rated controller config (the 2xlarge is an 8-vCPU slice of one
socket, so per-instance channel count is nominal); these are semi-custom hyperscaler SKUs,
so the memory spec is that of the public platform sibling. Granite is AWS-provisioned at
DDR5-7200 (above Intel's catalog rating); Turin at DDR5-6000.

| Label | Instance | Microarchitecture | CPU model | Memory | Cores × SMT |
|-------|----------|-------------------|-----------|--------|:-----------:|
| amd-rome | c5a.2xlarge | AMD Zen 2 (Rome) | EPYC 7R32 | DDR4-3200, 8ch | 4 × 2 |
| amd-milan | m6a.2xlarge | AMD Zen 3 (Milan) | EPYC 7R13 | DDR4-3200, 8ch | 4 × 2 |
| amd-genoa | m7a.2xlarge | AMD Zen 4 (Genoa) | EPYC 9R14 | DDR5-4800, 12ch | 8 × 1 |
| amd-turin | m8a.2xlarge | AMD Zen 5 (Turin) | EPYC 9R45 | DDR5-6000, 12ch | 8 × 1 |
| intel-icelake | m6i.2xlarge | Intel Ice Lake | Xeon Platinum 8375C | DDR4-3200, 8ch | 4 × 2 |
| intel-sapphire | m7i.2xlarge | Intel Sapphire Rapids | Xeon Platinum 8488C | DDR5-4800, 8ch | 4 × 2 |
| intel-granite | m8i.2xlarge | Intel Granite Rapids | Xeon 6975P-C | DDR5-7200, 12ch | 4 × 2 |
| arm-graviton2 | m6g.2xlarge | Arm Neoverse-N1 | AWS Graviton2 | DDR4-3200, 8ch | 8 × 1 |
| arm-graviton3 | m7g.2xlarge | Arm Neoverse-V1 | AWS Graviton3 | DDR5-4800, 8ch | 8 × 1 |
| arm-graviton4 | m8g.2xlarge | Arm Neoverse-V2 | AWS Graviton4 | DDR5-5600, 12ch | 8 × 1 |

`Cores × SMT` is physical cores per socket × hardware threads per core; every box
totals 8 vCPUs. Note the topology split the sweep pins around: the DDR4 AMD parts
and all Intel parts expose 4 physical cores × 2 SMT threads, while the DDR5 AMD
parts and every Graviton expose 8 single-threaded cores. Pinning to physical
cores keeps the `fat`/`entries` ratio apples-to-apples within each machine.

## Auxiliary (not a benchmark target)

A throwaway GCP CPU box ran `ncu --import` to post-process the NSight Compute
captures into CSV (host-only, no GPU); a GCP profiling box also captured the A100
cost-surface row (Lambda blocked GPU profiling). Neither produced decode measurements.
