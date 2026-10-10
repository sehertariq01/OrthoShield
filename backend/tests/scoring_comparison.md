# Scoring Comparison Report — Fix 4 + Fix 5

> Generated from `145` DICOM files in `datasets/`

## Summary

| Metric | Value |
|--------|-------|
| Files scanned | 145 |
| Errors (could not parse) | 0 |
| Decision flips | 24 |

## Score Distribution (new engine)

> **You must choose `BLOCK_THRESHOLD` from this table.**
> Files ≥ threshold will be BLOCKED (excluding hard-blocks which always block).

| New score range | File count | % of total |
|-----------------|-----------|------------|
| 0 | 71 | 49.0% |
| 1-5 | 25 | 17.2% |
| 6-10 | 5 | 3.4% |
| 11-15 | 25 | 17.2% |
| 16-20 | 17 | 11.7% |
| 21-30 | 2 | 1.4% |
| 31-50 | 0 | 0.0% |
| 51-100 | 0 | 0.0% |

**Min:** 0.00 &nbsp; **Max:** 24.59 &nbsp; **Mean:** 5.31 &nbsp; **Median:** 2.73

## Decision Flips

| Filename | Old score | New score | Old decision | New decision | Notes |
|----------|-----------|-----------|--------------|--------------|-------|
| `datasets\archive\693_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\color3d_jpeg_baseline.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\empty_charset_LEI.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\emri_small.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['pixel_data_consistency', 'embedded_objects'] new_failed=['pixel_data_consistency', 'embedded_objects'] |
| `datasets\archive\emri_small_big_endian.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['pixel_data_consistency', 'embedded_objects'] new_failed=['pixel_data_consistency', 'embedded_objects'] |
| `datasets\archive\emri_small_jpeg_2k_lossless.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\emri_small_RLE.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\explicit_VR-UN.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\JPEG-LL.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\meta_missing_tsyntax.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\MR2_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\MR2_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\nested_priv_SQ.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\no_meta_group_length.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\priv_SQ.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\RG1_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_UNCI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_UNCR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG3_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG3_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\US1_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\US1_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\US-MONO2-8-8x-echo.dcm` | 16.85 | 16.39 | BLOCKED | CLEAN | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['timestamp_validity', 'pixel_data_consistency', 'embedded_objects'] new_failed=['timestamp_validity', 'pixel_data_consistency', 'embedded_objects'] |

## Full Results

| Filename | Old score | New score | Old decision | New decision | Flipped | Notes |
|----------|-----------|-----------|--------------|--------------|---------|-------|
| `datasets\archive\693_J2KI.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\693_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\693_UNCI.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\693_UNCR.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\bad_sequence.dcm` | 22.47 | 21.86 | BLOCKED | BLOCKED | no | old_failed=['uid_format', 'ml_anomaly_score', 'embedded_objects'] new_failed=['uid_format', 'ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\badVR.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\color-pl.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['timestamp_validity'] new_failed=['timestamp_validity'] |
| `datasets\archive\color-px.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['timestamp_validity'] new_failed=['timestamp_validity'] |
| `datasets\archive\color3d_jpeg_baseline.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\CT_small.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\eCT_Supplemental.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\empty_charset_LEI.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\emri_small.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['pixel_data_consistency', 'embedded_objects'] new_failed=['pixel_data_consistency', 'embedded_objects'] |
| `datasets\archive\emri_small_big_endian.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['pixel_data_consistency', 'embedded_objects'] new_failed=['pixel_data_consistency', 'embedded_objects'] |
| `datasets\archive\emri_small_jpeg_2k_lossless.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\emri_small_jpeg_2k_lossless_too_short.dcm` | 25.28 | 24.59 | BLOCKED | BLOCKED | no | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score', 'embedded_objects'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\emri_small_jpeg_ls_lossless.dcm` | 8.43 | 8.2 | CLEAN | CLEAN | no | old_failed=['ml_anomaly_score'] new_failed=['ml_anomaly_score'] |
| `datasets\archive\emri_small_RLE.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\explicit_VR-UN.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\ExplVR_BigEnd.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['timestamp_validity'] new_failed=['timestamp_validity'] |
| `datasets\archive\ExplVR_BigEndNoMeta.dcm` | 8.43 | 10.71 | BLOCKED | BLOCKED | no | old_failed=['magic_byte_structure'] new_failed=['magic_byte_structure'] |
| `datasets\archive\ExplVR_LitEndNoMeta.dcm` | 8.43 | 10.71 | BLOCKED | BLOCKED | no | old_failed=['magic_byte_structure'] new_failed=['magic_byte_structure'] |
| `datasets\archive\gdcm-US-ALOKA-16.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\gdcm-US-ALOKA-16_big.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\image_dfl.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\JPEG-LL.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\JPEG-lossy.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\JPEG2000.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\JPEG2000_UNC.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\JPGLosslessP14SV1_1s_1f_8b.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\liver.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\liver_1frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\liver_expb.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\liver_expb_1frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\meta_missing_tsyntax.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\mlut_18.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR-SIEMENS-DICOM-WithOverlays.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR2_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\MR2_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\MR2_UNCI.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\MR2_UNCR.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\MR_small.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR_small_bigendian.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR_small_expb.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR_small_implicit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR_small_jp2klossless.dcm` | 8.43 | 8.2 | CLEAN | CLEAN | no | old_failed=['ml_anomaly_score'] new_failed=['ml_anomaly_score'] |
| `datasets\archive\MR_small_jpeg_ls_lossless.dcm` | 8.43 | 8.2 | CLEAN | CLEAN | no | old_failed=['ml_anomaly_score'] new_failed=['ml_anomaly_score'] |
| `datasets\archive\MR_small_padded.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\MR_small_RLE.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\MR_truncated.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\nested_priv_SQ.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\no_meta.dcm` | 8.43 | 10.71 | BLOCKED | BLOCKED | no | old_failed=['magic_byte_structure'] new_failed=['magic_byte_structure'] |
| `datasets\archive\no_meta_group_length.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\OBXXXX1A.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\OBXXXX1A_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\OBXXXX1A_expb.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\OBXXXX1A_expb_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\OBXXXX1A_rle.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\OBXXXX1A_rle_2frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\OT-PAL-8-face.dcm` | 8.43 | 10.71 | BLOCKED | BLOCKED | no | old_failed=['magic_byte_structure'] new_failed=['magic_byte_structure'] |
| `datasets\archive\priv_SQ.dcm` | 14.04 | 13.66 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] new_failed=['required_tags', 'uid_format', 'ml_anomaly_score'] |
| `datasets\archive\reportsi.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['required_tags'] new_failed=['required_tags'] |
| `datasets\archive\reportsi_with_empty_number_tags.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['required_tags'] new_failed=['required_tags'] |
| `datasets\archive\RG1_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_UNCI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG1_UNCR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG3_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG3_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\RG3_UNCI.dcm` | 8.43 | 8.2 | CLEAN | CLEAN | no | old_failed=['ml_anomaly_score'] new_failed=['ml_anomaly_score'] |
| `datasets\archive\RG3_UNCR.dcm` | 8.43 | 8.2 | CLEAN | CLEAN | no | old_failed=['ml_anomaly_score'] new_failed=['ml_anomaly_score'] |
| `datasets\archive\rtdose.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\rtdose_1frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\rtdose_expb.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\rtdose_expb_1frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\rtdose_rle.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\rtdose_rle_1frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\rtplan.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['required_tags'] new_failed=['required_tags'] |
| `datasets\archive\rtplan_truncated.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['required_tags'] new_failed=['required_tags'] |
| `datasets\archive\rtstruct.dcm` | 8.43 | 10.71 | BLOCKED | BLOCKED | no | old_failed=['magic_byte_structure'] new_failed=['magic_byte_structure'] |
| `datasets\archive\SC_rgb.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_16bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_16bit_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_32bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_32bit_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_dcmtk_ebcr.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcr_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcyn1.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcyn1_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcyn2.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcyn2_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcynp.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcynp_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcys2.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcys2_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcys4.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_dcmtk_ebcys4_dcmd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_expb.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_expb_16bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_expb_16bit_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_expb_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_expb_32bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_expb_32bit_2frame.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_rgb_gdcm2k_uncompressed.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_gdcm_KY.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_jpeg_dcmtk.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_jpeg_gdcm.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_jpeg_lossy_gdcm.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle_16bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle_16bit_2frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle_2frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle_32bit.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_rle_32bit_2frame.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_small_odd.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_rgb_small_odd_jpeg.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\SC_ybr_full_422_uncompressed.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['pixel_data_consistency'] new_failed=['pixel_data_consistency'] |
| `datasets\archive\SC_ybr_full_uncompressed.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\archive\test-SR.dcm` | 2.81 | 2.73 | CLEAN | CLEAN | no | old_failed=['required_tags'] new_failed=['required_tags'] |
| `datasets\archive\US1_J2KI.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\US1_J2KR.dcm` | 19.66 | 19.13 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['ml_anomaly_score', 'embedded_objects'] new_failed=['ml_anomaly_score', 'embedded_objects'] |
| `datasets\archive\US1_UNCI.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\US1_UNCR.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\archive\vlut_04.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-01.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-02.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-03.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-04.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-05.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-06.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-07.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-08.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-09.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-10.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-11.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-12.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-13.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-14.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\prostate\MRI-PROSTATEx-0004\1-15.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-16.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-17.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-18.dcm` | 11.24 | 10.93 | CLEAN | CLEAN | no | old_failed=['embedded_objects'] new_failed=['embedded_objects'] |
| `datasets\prostate\MRI-PROSTATEx-0004\1-19.dcm` | 0.0 | 0.0 | CLEAN | CLEAN | no | — |
| `datasets\US-MONO2-8-8x-echo.dcm` | 16.85 | 16.39 | BLOCKED | CLEAN | ⚠️ YES | **DECISION FLIP** BLOCKED→CLEAN | old_failed=['timestamp_validity', 'pixel_data_consistency', 'embedded_objects'] new_failed=['timestamp_validity', 'pixel_data_consistency', 'embedded_objects'] |
