# Security Policy

## Supported versions

EEGauge is a small, actively developed project. Security fixes are applied to the
latest release on the `main` branch; older releases are not maintained.

| Version          | Supported |
| ---------------- | --------- |
| latest (`main`)  | yes       |
| older releases   | no        |

## Reporting a vulnerability

Please report security issues **privately** rather than opening a public issue.

- Preferred: email the maintainer at 202380099@psu.palawan.edu.ph, or
- use GitHub's private vulnerability reporting if it is enabled on this repository
  (the "Report a vulnerability" button under the Security tab).

Please include steps to reproduce and the affected version (`eegauge --version`).
I will acknowledge your report as soon as I can and work on a fix. This is a small
project maintained by one person, so please allow reasonable time for a response.

## Scope

EEGauge is research tooling for public datasets, not medical or production software.
The most relevant areas are how it parses external data files and how it downloads
data from MOABB and EEGDash sources, so reports about those are especially welcome.
