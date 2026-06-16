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

Candidate probing confirms that a discovered endpoint behaves like a supported Modbus TCP meter before promotion. Promotion creates a managed device record that can be polled by the backend.

Register maps may still require manual adjustment for specific meter vendors and firmware versions.

## Debug Tooling

Legacy Modbus debug tools are intentionally kept for real-device validation. Use them only against devices and networks where you have permission to test.
