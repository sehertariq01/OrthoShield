rule Suspicious_Embedded_Script
{
    meta:
        description = "Detects embedded script tags or JavaScript, unusual in medical DICOM files"
        severity = "high"

    strings:
        $script_tag = "<script" nocase
        $js_protocol = "javascript:" nocase
        $eval_call = "eval(" nocase

    condition:
        any of them
}

rule Suspicious_Executable_Signature
{
    meta:
        description = "Detects embedded Windows PE executable headers (MZ signature) inside a non-executable file"
        severity = "critical"

    strings:
        $mz_header = { 4D 5A }

    condition:
        $mz_header at 0 or $mz_header in (100..filesize)
}

rule Suspicious_Shell_Commands
{
    meta:
        description = "Detects common shell/command injection patterns"
        severity = "high"

    strings:
        $cmd1 = "cmd.exe"    nocase fullword
        $cmd2 = "/bin/sh"    nocase
        $cmd3 = "powershell" nocase fullword
        $cmd4 = "wget"       nocase fullword
        $cmd5 = "curl"       nocase fullword

    condition:
        any of them
}

rule EICAR_Test_String
{
    meta:
        description = "Detects the EICAR antivirus test string (for validating this rule engine works)"
        severity = "test"

    strings:
        $eicar = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

    condition:
        $eicar
}