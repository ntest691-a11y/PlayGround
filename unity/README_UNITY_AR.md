# 🔫 DEADZONE: Survivors — نسخة Unity (ويندوز أولًا)

نفس لعبة البايثون، معاد بناؤها بـ C# داخل Unity. المشهد يُبنى **تلقائيًا** من الكود — ما تحتاج تجهز شي في المحرر غير خطوة واحدة.

## التركيب (5 دقائق)
1. افتح **Unity Hub** → مشروع جديد **3D (Built-in Render Pipeline)** باسم `DEADZONE`
2. انسخ محتويات `unity/Assets/` إلى مجلد `Assets` في مشروعك (استبدل المجلدات)
3. تأكد من حزمة JSON: افتح **Window → Package Manager** وابحث عن **Newtonsoft Json** (`com.unity.nuget.newtonsoft-json`) — غالبًا موجودة افتراضيًا، لو لا ثبّتها
4. في الـ **Hierarchy**: كليك يمين → **Create Empty** وسمّه `Game`
5. حدده واضغط **Add Component** → اكتب `GameBootstrap` وأضفه
6. اضغط **Play** ▶ — العب!

## التحكم
`WASD` حركة | ماوس | زر أيسر إطلاق | `R` تعبئة | `1-4` أسلحة | `Q` تبديل | `M` مودات | `F1` مساعدة | `Esc` تحرير المؤشر/خروج

## تغيير الخريطة وعدد البوتات
حدد كائن `Game` — في الـ **Inspector** غيّر `Map Id` (`rooftop` / `warehouse` / أي خريطة من مود) و `Bots` (0-4).

## التصدير لويندوز (exe)
`File → Build Profiles` (أو Build Settings) → اختر **Windows** → **Build**. يطلع لك `.exe` جاهز.

## المودات (مثل L4D2)
مجلد المودات: `Assets/StreamingAssets/mods/` — وبعد البناء يصير بجانب الـ exe.
انسخ أي مجلد مود من نسخة البايثون (`game/mods/example_*`) — ملفات `weapons.json` و `zombies.json` و `maps.json` و `characters.json` والسكنات كلها متوافقة وتشتغل مباشرة (الأولوية للأعلى `priority`).

## ملاحظات
- **الموديلات المخصصة (VRM/GLB):** حاليًا الشخصيات والزومبي صناديق ملونة + السكنات ألوان. تركيب موديلات VRM يحتاج حزمة **UniVRM** و GLB يحتاج **GLTFUtility** — الخطوة الجاية بعد ما تثبت النسخة.
- **الأندرويد لاحقًا:** نفس المشروع — نضيف عصا لمس ونصدّر APK (إن شاء الله بعد الويندوز).
