# Troubleshooting

When the DLQ alarm fires, compare failed IDs with producer validation and receipt state. A reused job ID with changed content needs a producer fix. Correct the producer or message before authorizing replay. Compare receipt count before and after to detect duplicate processing.

Run the [local demo](../README.md#run-the-demo) from a clean checkout to compare the current output with the documented result.
