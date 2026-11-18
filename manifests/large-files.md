# Large files kept outside Git

These are too large for Git. They live in the recovery backup (`~/backup/vd-biodiversity-20260908/` and
`/media/data/backup/vd-biodiversity-20260908/` on bluemar-bio-xnx-2) and must also be kept offsite.
Checksums let you verify any copy: `sha256sum -c` against the lines below.

## Model weights (`/media/data/models`, mounted into the deepstream container)

```
056d35019f5e6e9570c533a090b936dd6ad37e1c2e7f5902d3eac4f9b55af99a  ./car/cal_trt.bin
6a3e007b86446f12dd46486baacd210223715490c2fdcb3e324ef0d8ad0563fe  ./car/resnet10.caffemodel
b8da373dfab1eeceb3eea888a01724b60545f26b07b897e632994e1a9d89e0d5  ./car/resnet10.prototxt
0634fd400e78f67a42ef9321beb4df81641efda993a073ec40358a3892a6f328  ./models-lock.json
26e6ab9ab62b4fcc45a39dc51c283116c9df687444981704c8544017ce5661a9  ./plant/labels.txt
57010a92c4426eef830789688b445f9659767f2e2383db45f35e8d3b82687141  ./plant/model_card.md
e07578aad2cd9fc882aa7939e927d3a86a4f92e475ae5d0e27b2254675f421e7  ./plant/model.onnx
2415a8549c5eed159e44df6021a3d1ef07823458a08716c4713c6100582d189d  ./roadkill/labels.txt
0d652ef947e7d2c0b63bf8cc634435fe0f83dc9832d8d498b649eb874912ae7c  ./roadkill/model_card.txt
95a89a3cc86176a50f5f0ab2986e12bc818175569aecd537ea9931fa1126261b  ./roadkill/model_layers.txt
cb74603b538f513f54a572387fc4f5cf603e4fa635ddb8241ffa16cb3ca0cbf8  ./roadkill/pgie_config.txt
acfab916b1e3b55c32c2502d3fcf4fb8a69508e93744844264bd758a3867ca8e  ./roadkill/yolov8m.onnx
```

TensorRT `.engine` files are generated on the device on first start and are not needed in a backup.

## Container images

| Image | Image ID | Size |
|---|---|---|
| `europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base` | `fcded2a42c5e` | 5.73GB |
| `europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gcs:base` | `aa294dcf3b92` | 867MB |
| `europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base` | `5539ac692e3d` | 853MB |

Saved archives (restore with `gunzip -c <file> | docker load`):

```
3d29474064ca4603e35f767fb36449fda709210df6e15967946e29e8f6eabaf5  deepstream-l4t-base.tar.gz
1586bbdd6fa8add626a8c411cf8441e157bc8a2b0946efe4c444b2e8397c7f56  gcs-base.tar.gz
167feb00e6f3fe4934fb6762484008aa43da1169b5103217a2914ba6ee5a9f8b  gps-base.tar.gz
```

## Git history

```
45bdaae4cdfd82f83b9d666dceefb8ca45c7442d04a9ce8755f1c226ac3f680e  vd-biodiversity.bundle
```

The bundle is the untouched original of Trifork's repository, all 100 branches. Keep it as the
forensic record, whatever is decided about the history in this repository
(see [the journal](../journal/2026-11-16-credentials-in-trifork-history.md)).
