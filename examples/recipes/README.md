# Device recipe library

Build named device patterns with `spec_builder`, validate, and load via the pipeline.

| Recipe | Type | Params |
|--------|------|--------|
| [gain](gain/) | audio_effect | Gain |
| [tone_lowpass](tone_lowpass/) | audio_effect | Tone |
| [saturator_drive_tone](saturator_drive_tone/) | audio_effect | Drive, Tone, Mix |
| [delay_feedback](delay_feedback/) | audio_effect | Time, Feedback, Mix |
| [simple_lfo](simple_lfo/) | audio_effect | Rate, Depth |
| [midi_arp](midi_arp/) | midi_effect | Rate, Octaves |
| [mono_synth](mono_synth/) | instrument | Pitch |
| [noise_gate](noise_gate/) | audio_effect | Threshold, Attack, Release |

## Build every recipe (offline T0)

```bash
for d in examples/recipes/*/; do
  ./venv/bin/python "$d/build.py"
  ./venv/bin/python scripts/validate_spec.py "$d/spec.json"
  ./venv/bin/python tooling/m4l_pipeline.py build "$d/spec.json" "/tmp/$(basename "$d").amxd"
done
```

## Load in Live (T3)

```bash
./venv/bin/python scripts/m4l_verify.py --spec examples/recipes/gain/spec.json --expect-params Gain
```

See [`docs/AGENT_IMPLEMENTATION_PLAN.md`](../docs/AGENT_IMPLEMENTATION_PLAN.md) for the full v2 plan.
