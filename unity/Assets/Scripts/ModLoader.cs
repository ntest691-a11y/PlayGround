using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// L4D2-style mod loader (folder mods inside StreamingAssets/mods).
/// Each mod: mod.json + optional weapons/zombies/maps/characters/
/// player_skins/zombie_skins/weapon_skins .json files + assets/ models.
/// Higher "priority" wins on conflicts. Pure C#, no scene refs.
/// </summary>
public class ModLoader
{
    [Serializable]
    public class Manifest
    {
        public string id = "";
        public string name = "";
        public string version = "1.0.0";
        public string author = "unknown";
        public string description = "";
        public int priority = 0;
        public bool enabled_by_default = true;
    }

    public class Mod
    {
        public string id = "";
        public string dirPath = "";
        public Manifest manifest = new Manifest();
        public bool enabled = true;
        public Dictionary<string, JObject> weapons = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> zombies = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> maps = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> characters = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> playerSkins = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> zombieSkins = new Dictionary<string, JObject>();
        public Dictionary<string, JObject> weaponSkins = new Dictionary<string, JObject>();
    }

    public List<Mod> mods = new List<Mod>();
    private static readonly string[] DataFiles = {
        "weapons.json", "zombies.json", "maps.json", "characters.json",
        "player_skins.json", "zombie_skins.json", "weapon_skins.json"
    };

    public string ModsRoot => Path.Combine(Application.streamingAssetsPath, "mods");

    public void Scan()
    {
        mods.Clear();
        if (!Directory.Exists(ModsRoot))
        {
            Directory.CreateDirectory(ModsRoot);
            return;
        }
        foreach (var dir in Directory.GetDirectories(ModsRoot))
        {
            string mf = Path.Combine(dir, "mod.json");
            if (!File.Exists(mf)) continue;
            try
            {
                var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(mf));
                if (manifest == null) continue;
                if (string.IsNullOrEmpty(manifest.id))
                    manifest.id = Path.GetFileName(dir);
                var mod = new Mod { id = manifest.id, dirPath = dir, manifest = manifest, enabled = manifest.enabled_by_default };
                foreach (var df in DataFiles)
                {
                    string fp = Path.Combine(dir, df);
                    if (!File.Exists(fp)) continue;
                    try
                    {
                        var obj = JObject.Parse(File.ReadAllText(fp));
                        foreach (var prop in obj.Properties())
                        {
                            if (prop.Value is JObject jo)
                                GetTable(mod, df)[prop.Name] = jo;
                        }
                    }
                    catch (Exception e) { Debug.LogWarning($"[Mods] bad {df} in {mod.id}: {e.Message}"); }
                }
                mods.Add(mod);
            }
            catch (Exception e) { Debug.LogWarning($"[Mods] bad manifest in {dir}: {e.Message}"); }
        }
        mods.Sort((a, b) => b.manifest.priority.CompareTo(a.manifest.priority));
    }

    private Dictionary<string, JObject> GetTable(Mod m, string file)
    {
        switch (file)
        {
            case "weapons.json": return m.weapons;
            case "zombies.json": return m.zombies;
            case "maps.json": return m.maps;
            case "characters.json": return m.characters;
            case "player_skins.json": return m.playerSkins;
            case "zombie_skins.json": return m.zombieSkins;
            default: return m.weaponSkins;
        }
    }

    public IEnumerable<Mod> Enabled()
    {
        foreach (var m in mods) if (m.enabled) yield return m;
    }

    public Dictionary<string, JObject> Merged(Func<Mod, Dictionary<string, JObject>> pick, Dictionary<string, JObject> vanilla)
    {
        var out_ = new Dictionary<string, JObject>(vanilla);
        var list = new List<Mod>(Enabled());
        list.Reverse(); // low priority first so high priority overwrites
        foreach (var m in list)
            foreach (var kv in pick(m))
                out_[kv.Key] = kv.Value;
        return out_;
    }

    /// Resolve "assets/x.glb" inside the owning mod folder. Returns abs path or null.
    public string ResolveAsset(string modId, string rel)
    {
        if (string.IsNullOrEmpty(rel)) return null;
        foreach (var m in mods)
        {
            if (m.id != modId) continue;
            string cand = Path.Combine(m.dirPath, rel.Replace('/', Path.DirectorySeparatorChar));
            if (File.Exists(cand)) return cand;
        }
        return null;
    }

    public string OwnerOf(Func<Mod, Dictionary<string, JObject>> pick, string key)
    {
        foreach (var m in Enabled())
            if (pick(m).ContainsKey(key)) return m.id;
        return null;
    }
}
