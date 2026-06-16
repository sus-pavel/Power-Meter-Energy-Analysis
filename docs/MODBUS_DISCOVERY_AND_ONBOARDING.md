# Modbus Discovery and Onboarding

PowerMeter discovers and validates Modbus TCP devices before adding them to the managed-device list.

## Workflow

```text
network target -> discovery scan -> candidate -> probe/fingerprint -> promote -> managed device -> polling
```

## Discovery Safety

Use trusted local networks only. Prefer narrow IP ranges during beta validation, especially around real industrial devices.

Unit ID discovery should use the safest scan mode that can identify the device:

- known Unit ID when available;
- small Unit ID ranges for controlled networks;
- broader scans only during deliberate validation.

PowerMeter is a monitoring tool. It should not be used as a control system.

## Probing and Promotion

Candidate probing is config-first. PowerMeter starts from known values, such as host, port, Unit ID, configured register map, function code, data type, scaling, timeout, and polling interval. If a matching managed-device register map or `config/devices.yaml` entry exists, probing validates a small safe subset of that configuration.

PowerMeter does not invent register maps during candidate probing. It does not scan broad register ranges, guess vendor templates, or write Modbus registers. A successful numeric read from an unknown address is not enough to create a managed register.

Promotion only creates device registers from probe rows marked as validated from configuration. Vendor-default and generic probe outcomes are advisory and require manual mapping before polling.

## Modbus Device Identification

During candidate probing, PowerMeter attempts Modbus Function Code 43 / MEI type 14, Read Device Identification. When supported, it preserves fields such as:

- VendorName
- ProductCode
- MajorMinorRevision
- VendorUrl
- ProductName
- ModelName
- UserApplicationName

If FC43/14 is unsupported, probing continues with config-based register validation. The candidate records `vendor_identification_supported = false` and stores the error reason.

## Vendor Default Profiles

Vendor profile infrastructure lives in `backend/app/core/vendor_profiles.py`. The current profiles are conservative placeholders for common vendors and are marked as needing verification. Do not add a default register map unless it has been verified against real hardware or vendor documentation.

To add a verified vendor profile safely:

1. Confirm the exact vendor, model, firmware, function code, address mode, data type, byte order, word order, and scaling.
2. Add only required or validation registers that are safe read-only Modbus reads.
3. Test with a narrow candidate probe against one authorized device.
4. Confirm failed register reads are reported as validation failures, not valid mappings.
5. Document the source of the register map and any model or firmware limitations.

## Probe Result Quality

Probe results distinguish:

- `validated_from_config`: configured register read succeeded and decoded.
- `vendor_profile_matched`: vendor identity matched a placeholder profile, but no register map is confirmed.
- `generic_modbus_detected`: endpoint behaved like Modbus, but no profile is known.
- `partial_probe`: some configured checks passed and some failed.
- `unsupported_device_identification`: FC43/14 was not available.
- `register_validation_failed`: endpoint responded, but a configured register did not validate.
- `invalid_response`, `timeout`, `connection_failed`: transport or protocol failure states.

Register maps may still require manual adjustment for specific meter vendors and firmware versions.

## Debug Tooling

Legacy Modbus debug tools are intentionally kept for real-device validation. Use them only against devices and networks where you have permission to test.
