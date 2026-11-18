# Why does every restart take 13 minutes?

**Kind:** change · **Status:** RESOLVED (2026-09-08): the AI engines could not be cached, because the
model folder was read-only to the app. The models now live on the SSD; a restart takes 26 s.

## Cause

TensorRT compiles each model into a `.engine` file on first use and normally saves it beside the
model. The log showed `failed to serialize cude engine to file: …/models/plant/…engine` on every
start. In the image, the model folders belong to uid 1000, while the app runs as `app` (uid 116). The
three engines took ~12-13 min to build: plant ~7, car ~2, roadkill ~4.

## The first fix failed, and why

Pointing `model-engine-file` in the three `pgie_*.txt` at a writable folder moved only the *read*
path. `nvinfer` derives the *write* path from the model file's own folder and ignores
`model-engine-file`. The log showed both at once:

```
deserialize engine from file : /media/data/engines/model.onnx_b1_gpu0_fp32.engine        <- moved
failed to serialize cude engine to file:
  /workspaces/vd-biodiversity/bio/models/plant/model.onnx_b1_gpu0_fp32.engine            <- not moved
```

## The fix that works

Copy the models out of the image to `/media/data/models` (the container did this itself as
`app:shared`; 202,682,807 bytes, 12 files, identical) and mount that folder over the image's model
folder: one added line in `/opt/apps/deepstream/docker-compose.yaml`. The `pgie_*.txt` need no change.
Engines persisted (plant 129 MB, roadkill 148 MB, car 1.9 MB); the next restart deserialized all three
and reached `Running...` in **26 s**. The original compose file is kept as
`docker-compose.yaml.orig-20260908`.

## Side effect, found later

Fast restarts made a crash loop invisible to the LED; see
[why the LED was green during the outage](2026-10-23-why-was-the-led-green-during-the-outage.md).
