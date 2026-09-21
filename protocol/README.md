# protocol/

Versioned, human-readable artifacts that define how the parts of the system talk to each
other. Nothing here is Python. Everything here is reviewed as a contract, not as code.

This directory exists before the architecture does, because two things are already certain
from the development methodology (ADR-0003): there will be agent prompts, and there will be
structured payloads between components whose shape must be checked mechanically rather than
trusted.

| Subdirectory | Holds | Rule |
|---|---|---|
| `prompts/` | Agent system prompts, exactly as sent, one file per agent per version | A prompt that produced a reported result is never edited in place. Bump the version and keep the old file |
| `schemas/` | JSON Schema for every structured payload that crosses a component boundary | Every schema is paired with the prompt or component that emits it, and is validated in the test suite |

## Why prompts are protocol, not code

A prompt is an interface. Changing it changes the system's behaviour in ways no type checker
catches, and results are only comparable across runs that used the same prompt. Keeping
prompts here, versioned and separate from the code that sends them, makes that explicit and
makes "which prompt produced this figure" answerable.

## Why schemas are mandatory

The failure mode being designed against is a malformed or silently drifting payload that
downstream code accepts and misinterprets. A schema that is checked at the boundary turns
that into a loud failure at the point of origin. Payloads that are only described in prose
have no guard.

## Current contents

Empty. Both subdirectories are populated by the milestone that defines the first component
boundary, which does not exist until the charter is approved.
