## Iteration 1 Plan

Approach:
- Update the weather fetch/render code to match the DOD: temperatures in Celsius and daily low/max wind speeds for Moraga.
- Use hourly `wind_speed_10m` samples to derive each day's wind low/max because the daily API fields do not provide a daily minimum wind speed.
- Keep the diff small by updating the existing weather modules and tests rather than introducing a new package or shared abstraction.

Milestones:
1. Change forecast request parameters and parsing logic in the weather implementations.
2. Update rendered output and tests to reflect Celsius plus low/max wind output.
3. Verify the CLI works for `Moraga, CA`; if geocoding is flaky, add a narrow fallback for the default location.

Open questions:
- Wind units are still `mph`. The DOD only requires Celsius for temperature, so this iteration keeps existing wind units to avoid a broader output/API change.
- The repo has two weather code paths with overlapping logic. Consolidation is possible later, but not necessary for this iteration.
