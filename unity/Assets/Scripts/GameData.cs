using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>Vanilla data (mirrors the Python version) + merged mod data. No scene refs.</summary>
public class GameData
{
    public Dictionary<string, JObject> weapons;
    public Dictionary<string, JObject> zombies;
    public Dictionary<string, JObject> maps;
    public Dictionary<string, JObject> characters;
    public Dictionary<string, JObject> playerSkins;
    public Dictionary<string, JObject> zombieSkins;
    public Dictionary<string, JObject> weaponSkins;
    public List<string> loadout = new List<string>();
    public ModLoader loader;

    public GameData(ModLoader loader)
    {
        this.loader = loader;
        Refresh();
    }

    public void Refresh()
    {
        weapons = loader.Merged(m => m.weapons, VanillaWeapons());
        zombies = loader.Merged(m => m.zombies, VanillaZombies());
        maps = loader.Merged(m => m.maps, VanillaMaps());
        characters = loader.Merged(m => m.characters, VanillaCharacters());
        playerSkins = loader.Merged(m => m.playerSkins, new Dictionary<string, JObject>());
        zombieSkins = loader.Merged(m => m.zombieSkins, new Dictionary<string, JObject>());
        weaponSkins = loader.Merged(m => m.weaponSkins, new Dictionary<string, JObject>());

        loadout = new List<string> { "pistol", "smg" };
        foreach (var m in loader.Enabled())
            foreach (var kv in m.weapons)
                if (kv.Value.Value<bool>("starter") && !loadout.Contains(kv.Key) && weapons.ContainsKey(kv.Key))
                    loadout.Add(kv.Key);
    }

    // ---------- typed helpers (defaults match Python config) ----------
    public static float F(JObject o, string k, float d) { try { var t = o[k]; return t == null ? d : (float)t; } catch { return d; } }
    public static int I(JObject o, string k, int d) { try { var t = o[k]; return t == null ? d : (int)t; } catch { return d; } }
    public static string S(JObject o, string k, string d) { try { var t = o[k]; return t == null ? d : (string)t; } catch { return d; } }
    public static bool B(JObject o, string k, bool d) { try { var t = o[k]; return t == null ? d : (bool)t; } catch { return d; } }

    public static Color C(JObject o, string k, Color d)
    {
        try
        {
            var t = o[k] as JArray;
            if (t == null || t.Count < 3) return d;
            return new Color((float)t[0], (float)t[1], (float)t[2], 1f);
        }
        catch { return d; }
    }

    public static float[] V3(JObject o, string k, float[] d)
    {
        try
        {
            var t = o[k] as JArray;
            if (t == null || t.Count < 3) return d;
            return new float[] { (float)t[0], (float)t[1], (float)t[2] };
        }
        catch { return d; }
    }

    // ---------- vanilla ----------
    private static JObject J(string json) => JObject.Parse(json);

    private static Dictionary<string, JObject> VanillaWeapons() => new Dictionary<string, JObject>
    {
        { "pistol", J(@"{"+"\"name\":\"Pistol\",\"damage\":25,\"magazine\":12,\"reserve\":120,\"fire_rate\":0.28,\"auto\":false,\"range\":60}") },
        { "smg", J(@"{"+"\"name\":\"SMG\",\"damage\":18,\"magazine\":30,\"reserve\":240,\"fire_rate\":0.11,\"auto\":true,\"range\":55}") },
        { "shotgun", J(@"{"+"\"name\":\"Shotgun\",\"damage\":12,\"pellets\":8,\"magazine\":8,\"reserve\":64,\"fire_rate\":0.9,\"auto\":false,\"range\":25}") },
        { "rifle", J(@"{"+"\"name\":\"Rifle\",\"damage\":32,\"magazine\":30,\"reserve\":210,\"fire_rate\":0.14,\"auto\":true,\"range\":80}") },
    };

    private static Dictionary<string, JObject> VanillaZombies() => new Dictionary<string, JObject>
    {
        { "common", J(@"{"+"\"name\":\"Common\",\"hp\":100,\"speed\":3.2,\"damage\":12,\"attack_range\":2.0,\"attack_rate\":1.0,\"score\":100,\"color\":[0.3,0.6,0.3],\"scale\":1.0}") },
        { "runner", J(@"{"+"\"name\":\"Runner\",\"hp\":60,\"speed\":6.0,\"damage\":8,\"attack_range\":1.8,\"attack_rate\":0.7,\"score\":150,\"color\":[0.7,0.3,0.2],\"scale\":0.9}") },
        { "brute", J(@"{"+"\"name\":\"Brute\",\"hp\":350,\"speed\":2.0,\"damage\":30,\"attack_range\":2.4,\"attack_rate\":1.6,\"score\":300,\"color\":[0.4,0.2,0.5],\"scale\":1.5}") },
    };

    private static Dictionary<string, JObject> VanillaCharacters() => new Dictionary<string, JObject>
    {
        { "survivor_1", J(@"{"+"\"name\":\"Rookie\",\"color\":[0.2,0.4,0.8],\"scale\":1.0}") },
        { "survivor_2", J(@"{"+"\"name\":\"Doc\",\"color\":[0.8,0.4,0.2],\"scale\":1.0}") },
        { "survivor_3", J(@"{"+"\"name\":\"Ghost\",\"color\":[0.4,0.8,0.4],\"scale\":1.0}") },
        { "survivor_4", J(@"{"+"\"name\":\"Veteran\",\"color\":[0.7,0.7,0.2],\"scale\":1.0}") },
    };

    private static Dictionary<string, JObject> VanillaMaps() => new Dictionary<string, JObject>
    {
        { "rooftop", J(@"{""name"":""Rooftop Siege"",""ground_size"":60,""ground_color"":[0.18,0.19,0.22],
            ""player_spawn"":[0,1.2,10],""spawn_points"":[[-10,1,-15],[10,1,-15],[0,1,-18],[-15,1,0],[15,1,0]],
            ""props"":[{""pos"":[0,0.5,-10],""scale"":[8,1,1],""color"":[0.3,0.3,0.35]},{""pos"":[-8,1.5,5],""scale"":[2,3,2],""color"":[0.35,0.3,0.25]},{""pos"":[8,1,6],""scale"":[2,2,2],""color"":[0.3,0.35,0.3]}],
            ""waves"":[{""count"":6,""types"":[""common""]},{""count"":10,""types"":[""common"",""runner""]},{""count"":14,""types"":[""common"",""runner"",""brute""]}]}") },
        { "warehouse", J(@"{""name"":""Abandoned Warehouse"",""ground_size"":50,""ground_color"":[0.22,0.18,0.14],
            ""player_spawn"":[0,1.2,8],""spawn_points"":[[-8,1,-14],[8,1,-14],[0,1,-15]],
            ""props"":[{""pos"":[0,1,0],""scale"":[3,2,3],""color"":[0.5,0.35,0.2]},{""pos"":[-6,1,-4],""scale"":[3,2,3],""color"":[0.45,0.32,0.18]},{""pos"":[6,1,-4],""scale"":[3,2,3],""color"":[0.45,0.32,0.18]}],
            ""waves"":[{""count"":8,""types"":[""common"",""runner""]},{""count"":12,""types"":[""common"",""runner"",""brute""]}]}") },
    };
}
