import pydicom
from pydicom.errors import InvalidDicomError

# Transfer Syntax UIDs that use compressed pixel data.
# For these, raw pixel length != Rows × Columns × BitsAllocated/8,
# so the pixel consistency check must be skipped.
COMPRESSED_TRANSFER_SYNTAXES = {
    "1.2.840.10008.1.2.4.50",   # JPEG Baseline (Process 1)
    "1.2.840.10008.1.2.4.51",   # JPEG Extended (Process 2 & 4)
    "1.2.840.10008.1.2.4.57",   # JPEG Lossless (Process 14)
    "1.2.840.10008.1.2.4.70",   # JPEG Lossless First-Order Prediction (SV1)
    "1.2.840.10008.1.2.4.80",   # JPEG-LS Lossless
    "1.2.840.10008.1.2.4.81",   # JPEG-LS Near-Lossless
    "1.2.840.10008.1.2.4.90",   # JPEG 2000 Lossless Only
    "1.2.840.10008.1.2.4.91",   # JPEG 2000
    "1.2.840.10008.1.2.5",      # RLE Lossless
}


def parse_dicom_metadata(file_path: str) -> dict:
    try:
        ds = pydicom.dcmread(file_path, force=False)
    except InvalidDicomError:
        return {
            "is_valid_dicom": False,
            "error": "File is not a valid DICOM file (invalid header/signature)"
        }
    except Exception as e:
        return {
            "is_valid_dicom": False,
            "error": f"Failed to parse file: {str(e)}"
        }

    # Determine transfer syntax and whether pixel data is compressed
    transfer_syntax_uid = ""
    if hasattr(ds, "file_meta") and ds.file_meta is not None:
        transfer_syntax_uid = str(getattr(ds.file_meta, "TransferSyntaxUID", ""))
    is_compressed = transfer_syntax_uid in COMPRESSED_TRANSFER_SYNTAXES

    metadata = {
        "is_valid_dicom": True,
        "sop_instance_uid":    str(getattr(ds, "SOPInstanceUID", None)),
        "sop_class_uid":       str(getattr(ds, "SOPClassUID", None)),
        "modality":            str(getattr(ds, "Modality", None)),
        "manufacturer":        str(getattr(ds, "Manufacturer", None)),
        "study_description":   str(getattr(ds, "StudyDescription", None)),
        "patient_name":        str(getattr(ds, "PatientName", None)),
        "referring_physician": str(getattr(ds, "ReferringPhysicianName", None)),
        "institution_name":    str(getattr(ds, "InstitutionName", None)),
        "rows":                getattr(ds, "Rows", None),
        "columns":             getattr(ds, "Columns", None),
        "bits_allocated":      getattr(ds, "BitsAllocated", None),
        "bits_stored":         getattr(ds, "BitsStored", None),
        "samples_per_pixel":   getattr(ds, "SamplesPerPixel", None),
        "pixel_data_present":  hasattr(ds, "PixelData"),
        "total_tag_count":     len(ds),
        "study_date":          str(getattr(ds, "StudyDate", None)),
        "pixel_data_length":   len(ds.PixelData) if hasattr(ds, "PixelData") else 0,
        "transfer_syntax_uid": transfer_syntax_uid,
        "is_compressed":       is_compressed,
    }

    return metadata
