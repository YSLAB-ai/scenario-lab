# Scenario Lab Limitations

- Output quality depends heavily on the approved evidence packet.
- Output quality depends heavily on the depth and quality of the domain pack.
- Replay calibration is stronger in some domains than others.
- Current replay calibration is regression coverage, not verified real-world forecast skill. The latest checked suite has `40` cases, `28` historically anchored cases, and `2` evidence-source mismatches, so affected domains are flagged for attention rather than treated as fully clean.
- Some replay domains still have concentrated expected outcomes. This is useful for regression protection, but it should not be read as broad empirical validation.
- Public replay source URLs can move, block automated checks, or require browser access. The checked-in replay text is the executable corpus; source links remain supporting references.
- The system is designed to improve over time through community contributions and protected domain-evolution workflows.
- This is an experimental preview, not a production forecasting guarantee.
- OCR-backed PDF ingestion is intentionally deferred in the current public preview.

## License and use limits

- The public repository is licensed under the `MIT License`.
- Scenario Lab is provided for experimental, educational, and research use. It is not a prediction product or a substitute for professional judgment.
- The software is provided `as is`, without warranty, under the terms of the [MIT License](../LICENSE).
