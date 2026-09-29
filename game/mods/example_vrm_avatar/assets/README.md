# Assets — حط موديلاتك هنا

## أنواع الموديلات المدعومة
| النوع | الحالة |
|---|---|
| `.glb` / `.gltf` | شغال مباشرة (يحتاج `panda3d-gltf` — موجود في requirements) |
| `.obj` / `.egg` / `.bam` / `.dae` | شغال مباشرة |
| `.vrm` | يشتغل تلقائيًا (VRM مبني على glTF — اللعبة تنسخه كـ `.glb` وتحمله، بدون تحويل يدوي). الريغ البشري يظهر كما هو بدون retargeting |
| `.fbx` | **ما يشتغل مباشرة** — حوّله مرة واحدة بـ `fbx2gltf` أو Blender إلى `.glb` ثم اربط الـ `.glb` |

## من وين تجيب VRM؟
- VRoid Studio (مجاني): صمم أفاتار وصدّر `.vrm`
- مواقع: Booth.pm / NicoNico — انسخ ملف `.vrm` هنا وحدّث `characters.json`

## مثال (characters.json)
```json
{"vrm_hero": {"name": "VRM Hero", "model": "assets/hero.vrm", "color": [0.6,0.4,0.9], "scale": 1.0}}
```
ثم: `python main.py --character vrm_hero`
