# 🔫 DEADZONE: Survivors — لعبة زومبي 3D للكمبيوتر تدعم المودات مثل L4D2

## التشغيل (Desktop)
```bash
cd game
pip install -r requirements.txt
python main.py                 # خريطة rooftop
python main.py --map neon_arena
python main.py --list-mods     # عرض المودات المثبتة
./run.sh --map warehouse
```

## التحكم
`WASD` حركة | ماوس نظر | زر أيسر إطلاق | `R` تعبئة | `1-4` أسلحة | `Q` تبديل | `M` قائمة المودات | `F1` مساعدة | `Esc` خروج

## نظام المودات (مثل L4D2 VPK / Workshop)
مجلد المودات: `game/mods/`

**صيغتان مدعومتان:**
1. مجلد: `mods/my_mod/mod.json` + ملفات اختيارية
2. مضغوط: `mods/my_mod.dzm` (ملف zip — نفس فكرة `.vpk` في L4D2)

**ملفات المود:**
| ملف | الوظيفة |
|---|---|
| `mod.json` | الاسم/الإصدار/الكاتب/الأولوية `priority` |
| `weapons.json` | أسلحة جديدة أو تعديل أسلحة `{id: {damage, magazine, ...}}` |
| `zombies.json` | زومبي جدد `{id: {hp, speed, damage, ...}}` — **كلهم يقبلون `model` مخصص** |
| `maps.json` | خرائط جديدة `{id: {props, spawn_points, waves}}` |
| `characters.json` | **شخصيات لاعب جديدة** `{id: {name, model, color, scale}}` — كل الشخصيات قابلة للتعديل |
| `player_skins.json` | سكنات للشخصيات `{id: {character, model, texture, color}}` |
| `zombie_skins.json` | سكنات زومبي `{id: {zombie, model, texture, color}}` |
| `weapon_skins.json` | **سكنات أسلحة** `{id: {weapon, model, texture, color}}` |
| `assets/` | موديلات + تكستشرات: `.glb/.gltf/.obj` مباشرة، `.vrm` تلقائي، `.fbx` حوّله لـ `.glb` |
| `hooks.py` | سكربت مثل VScript: `on_wave_start`, `on_zombie_spawn`, `modify_damage`, `on_player_damage` |

## الشخصيات والسكنات (جديد)
```bash
python main.py --list-skins                        # عرض كل الشخصيات والسكنات
python main.py --character vrm_hero                # العب بشخصية VRM
python main.py --weapon-skin rifle:gold --zombie-skin common:neon
```
- **VRM:** انسخ ملف `.vrm` من VRoid Studio إلى `assets/` واربطه في `characters.json` — يشتغل بدون تحويل
- **GLB/OBJ:** حط الملف في `assets/` واربطه بنفس الطريقة
- **FBX:** حوّله بـ fbx2gltf أو Blender إلى `.glb` أولًا

الأولوية: الرقم الأكبر يكسب عند التعارض. التفعيل/التعطيل يُحفظ في `mods/enabled.json`.

## مودات مثال مشحونة مع اللعبة
- `example_golden_ak` — سلاح Golden AK-47 (سلاح جديد starter)
- `example_tank` — زومبي Tank + سكربت hooks (كل 3 موجات يضيف Tank + درع 10%)
- `example_neon_arena` — خريطة `neon_arena` جديدة — جرّب: `python main.py --map neon_arena`
- `example_skins_pack` — سكنات أسلحة (`rifle:gold`) + سكنات زومبي (`common:neon`)
- `example_vrm_avatar` — شخصية VRM (`--character vrm_hero`) — بدّل ملف `assets/hero.vrm` بموديل VRoid حقيقي

## صناعة مود جديد
```bash
cd game
python tools/new_mod.py my_cool_gun --pack   # ينشئ مجلد + ملف .dzm جاهز للمشاركة
```
ثم عدّل `mods/my_cool_gun/weapons.json` وأعد التشغيل. شارك ملف `.dzm` مع أصدقائك — يضعونه في `mods/` ويعمل فورًا (مثل ملفات VPK).

## الاختبارات (بدون فتح نافذة 3D)
```bash
cd game
python -m pytest tests/ -v
```
