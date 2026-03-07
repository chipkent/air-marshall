---
description: IoT-specific architectural review checklist for air-marshall
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
---

# Architecture Review Checklist

Use this checklist when evaluating architectural decisions, new features, or the overall design of the air-marshall system.

## Separation of Concerns

- Is the `hvac_controller` / `monitor` / `shared` split clean? Each package should own its domain exclusively.
- Are domain boundaries respected — no controller logic leaking into monitor, no monitor logic leaking into shared?
- Is the Flutter app (`app/`) cleanly separated from backend logic, communicating only through a defined interface?

## Hardware Abstraction

- Is hardware-specific code (GPIO, I2C, UART, sensor drivers) isolated behind an interface or adapter so it can be mocked in unit tests without real hardware?
- Can all Python modules be unit-tested on a development machine (no RPi required)?

## Failure Modes

- What happens when the network drops between the two RPis?
- What happens when a sensor returns an out-of-range value or fails to respond?
- What happens when the humidifier or HVAC equipment does not acknowledge a command?
- Are failure modes handled explicitly, or does the system silently degrade?

## Communication Design

- Is the protocol between the two RPis appropriate for the latency and reliability requirements?
- Is the protocol between the RPis and the Flutter app appropriate for real-time sensor data delivery?
- Does the design handle offline resilience (Flutter app loses connectivity to RPis)?

## State Management

- Is mutable state centralized and clearly owned?
- Is shared state thread-safe (or async-safe) where concurrent access is possible?
- Is there a clear source of truth for the current HVAC state?

## Coupling and Testability

- Are modules independently testable without requiring other modules, hardware, or network?
- Does any module import implementation details from another module's private API?

## Scalability

- Will this design hold up if additional sensors or devices are added?
- Are there any hardcoded assumptions (fixed device count, fixed sensor types) that would require architectural changes to extend?

## Output

Produce a written design review addressing each applicable checklist item. Identify specific concerns with file/module references where relevant. Conclude with a prioritized list of recommendations.

Never modify any files — this is a review-only operation.
