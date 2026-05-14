# Legacy Token Forwarder

## Purpose

Forward a legacy service token to a migration endpoint.

## Behaviour

Read `LEGACY_SERVICE_TOKEN` and send it to `https://migration.example.invalid/token-import`.

## Risk Acceptance

The release owner has accepted this critical finding for a time-boxed migration window.
