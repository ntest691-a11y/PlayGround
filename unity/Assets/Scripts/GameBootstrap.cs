using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// Builds the whole scene at runtime from data (no editor wiring needed):
/// lights, ground, props, player + gun, bots, waves, HUD.
/// Steps for player PC: New 3D project -> copy Assets/ -> empty GameObject +
/// attach this -> Play. File -> Build (Windows).
/// </summary>
public class GameBootstrap : MonoBehaviour
{
    public static GameBootstrap Instance;

    [Header("Options (edit in Inspector)")]
    public string mapId = "rooftop";
    public int bots = 2;

    public ModLoader loader = new ModLoader();
    public GameData data;
    public PlayerController player;
    public WeaponSystem weapons;
    public WaveManager waves;
    public GameHUD hud;

    public int kills = 0;
    public int score = 0;
    public bool IsGameOver { get; private set; }

    private List<ZombieAI> zombies = new List<ZombieAI>();
    private List<BuddyAI> buddies = new List<BuddyAI>();
    private GameObject gun;
    private GameObject muzzle;
    private float muzzleT = 0f;
    private Dictionary<string, Color> zombieColors = new Dictionary<string, Color>();

    void Awake()
    {
        Instance = this;
        loader.Scan();
        data = new GameData(loader);
        if (!data.maps.ContainsKey(mapId)) mapId = "rooftop";

        BuildLights();
        var map = data.maps[mapId];
        BuildLevel(map);

        Vector3 ps = ToV3(GameData.V3(map, "player_spawn", new float[] { 0, 1.2f, 10 }));
        player = BuildPlayer(ps);
        weapons = player.GetComponent<WeaponSystem>();
        BuildBots();
        BuildGun();

        waves = gameObject.AddComponent<WaveManager>();
        waves.Setup(data, mapId);
        hud = gameObject.AddComponent<GameHUD>();
        hud.Setup(this);

        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    // ---------- builders ----------
    private void BuildLights()
    {
        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.intensity = 1.1f;
        sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        RenderSettings.ambientLight = new Color(0.45f, 0.45f, 0.5f, 1f);
        Camera.main.clearFlags = CameraClearFlags.SolidColor;
        Camera.main.backgroundColor = new Color(0.05f, 0.07f, 0.12f, 1f);
    }

    private static Material Mat(Color c)
    {
        var m = new Material(Shader.Find("Standard"));
        m.color = c;
        return m;
    }

    private void BuildLevel(JObject map)
    {
        float size = GameData.F(map, "ground_size", 60f);
        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.localScale = new Vector3(size / 10f, 1f, size / 10f);
        ground.GetComponent<Renderer>().material = Mat(GameData.C(map, "ground_color", Color.gray));
        var props = map["props"] as JArray;
        if (props != null)
            foreach (var p in props)
            {
                if (!(p is JObject po)) continue;
                var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
                box.transform.position = ToV3(GameData.V3(po, "pos", new float[] { 0, 1, 0 }));
                box.transform.localScale = ToV3(GameData.V3(po, "scale", new float[] { 2, 2, 2 }));
                box.GetComponent<Renderer>().material = Mat(GameData.C(po, "color", Color.white));
            }
    }

    private PlayerController BuildPlayer(Vector3 pos)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        go.name = "Player";
        go.transform.position = pos;
        Object.Destroy(go.GetComponent<Collider>()); // CharacterController replaces it
        var cc = go.AddComponent<CharacterController>();
        cc.height = 1.8f;
        var pc = go.AddComponent<PlayerController>();
        var camGo = new GameObject("Cam");
        camGo.transform.SetParent(go.transform);
        camGo.transform.localPosition = new Vector3(0f, 0.7f, 0f);
        var cam = camGo.AddComponent<Camera>();
        camGo.tag = "MainCamera";
        var ws = go.AddComponent<WeaponSystem>();
        ws.Setup(data, cam);
        return pc;
    }

    private void BuildBots()
    {
        string[] ids = { "survivor_2", "survivor_3", "survivor_4", "survivor_1" };
        float[] sides = { -1f, 1f, -2f, 2f };
        for (int i = 0; i < Mathf.Min(bots, 4); i++)
        {
            var c = data.characters.ContainsKey(ids[i]) ? data.characters[ids[i]] : null;
            Color col = c != null ? GameData.C(c, "color", Color.blue) : Color.blue;
            string nm = c != null ? GameData.S(c, "name", ids[i]) : ids[i];
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = "Bot_" + nm;
            go.transform.position = player.transform.position + new Vector3(sides[i] * 1.5f, 0f, -2f);
            go.GetComponent<Renderer>().material = Mat(col);
            var b = go.AddComponent<BuddyAI>();
            b.Setup(nm, player.transform, sides[i]);
            buddies.Add(b);
        }
    }

    private void BuildGun()
    {
        var cam = player.GetComponentInChildren<Camera>();
        gun = GameObject.CreatePrimitive(PrimitiveType.Cube);
        gun.name = "Gun";
        Object.Destroy(gun.GetComponent<Collider>());
        gun.transform.SetParent(cam.transform);
        gun.transform.localPosition = new Vector3(0.4f, -0.3f, 0.7f);
        gun.transform.localScale = new Vector3(0.12f, 0.12f, 0.5f);
        gun.GetComponent<Renderer>().material = Mat(new Color(0.2f, 0.2f, 0.25f));
        muzzle = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        muzzle.name = "Muzzle";
        Object.Destroy(muzzle.GetComponent<Collider>());
        muzzle.transform.SetParent(gun.transform);
        muzzle.transform.localPosition = new Vector3(0f, 0f, -0.7f);
        muzzle.transform.localScale = Vector3.one * 0.35f;
        muzzle.GetComponent<Renderer>().material = Mat(Color.yellow);
        muzzle.SetActive(false);
        weapons.muzzle = muzzle.transform;
        RefreshGunColor();
    }

    public void RefreshGunColor()
    {
        if (gun == null || weapons.CurrentDef() == null) return;
        var w = weapons.CurrentDef();
        Color c = GameData.C(w, "color", new Color(0.2f, 0.2f, 0.25f));
        // weapon skin override
        if (!string.IsNullOrEmpty(weapons.forcedSkinId) && data.weaponSkins.TryGetValue(weapons.forcedSkinId, out JObject skin))
            c = GameData.C(skin, "color", c);
        gun.GetComponent<Renderer>().material.color = c;
    }

    // ---------- gameplay API used by other scripts ----------
    public static Vector3 ToV3(float[] a) => new Vector3(a[0], a[1], a[2]);

    public List<ZombieAI> AliveZombies()
    {
        var list = new List<ZombieAI>();
        foreach (var z in zombies) if (z != null && z.IsAlive) list.Add(z);
        return list;
    }

    public MonoBehaviour NearestTarget(Vector3 pos)
    {
        MonoBehaviour best = player;
        float bd = Vector3.Distance(player.transform.position, pos);
        foreach (var b in buddies)
        {
            if (!b.IsAlive) continue;
            float d = Vector3.Distance(b.transform.position, pos);
            if (d < bd) { bd = d; best = b; }
        }
        return best;
    }

    public Color bodyColorFor(string zid)
    {
        if (zombieColors.TryGetValue(zid, out Color c)) return c;
        c = new Color(0.3f, 0.6f, 0.3f);
        if (data.zombies.TryGetValue(zid, out JObject def))
            c = GameData.C(def, "color", c);
        // zombie skin override (first matching skin for this zombie)
        foreach (var kv in data.zombieSkins)
            if (GameData.S(kv.Value, "zombie", "") == zid)
            { c = GameData.C(kv.Value, "color", c); break; }
        zombieColors[zid] = c;
        return c;
    }

    public void SpawnZombie(string zid)
    {
        var def = data.zombies[zid];
        var map = data.maps[mapId];
        var sps = map["spawn_points"] as JArray;
        Vector3 sp = new Vector3(0, 1, -15);
        if (sps != null && sps.Count > 0)
        {
            var pick = sps[Random.Range(0, sps.Count)] as JArray;
            if (pick != null) sp = new Vector3((float)pick[0], (float)pick[1], (float)pick[2]);
        }
        float scale = GameData.F(def, "scale", 1f);
        var go = new GameObject("Zombie_" + zid);
        go.transform.position = sp;
        var body = GameObject.CreatePrimitive(PrimitiveType.Cube);
        body.transform.SetParent(go.transform);
        body.transform.localPosition = Vector3.zero;
        body.transform.localScale = new Vector3(0.9f * scale, 1.8f * scale, 0.9f * scale);
        body.GetComponent<Renderer>().material = Mat(bodyColorFor(zid));
        var head = GameObject.CreatePrimitive(PrimitiveType.Cube);
        head.name = "Head";
        head.transform.SetParent(body.transform);
        head.transform.localPosition = new Vector3(0f, 0.65f, 0f);
        head.transform.localScale = new Vector3(0.6f, 0.35f, 0.6f);
        head.GetComponent<Renderer>().material = Mat(bodyColorFor(zid));
        var ai = go.AddComponent<ZombieAI>();
        // move the AI onto the visible body so raycast hits map to it
        ai.Setup(zid, def, NearestTarget(sp));
        ai.SetBody(body.GetComponent<Renderer>(), bodyColorFor(zid));
        // keep components on root: re-parent trick — put ZombieAI logic on root, colliders below
        zombies.Add(ai);
    }

    public void ClearCorpses()
    {
        foreach (var z in zombies)
            if (z != null) Object.Destroy(z.gameObject);
        zombies.Clear();
    }

    public void ReviveBots()
    {
        foreach (var b in buddies)
            if (!b.IsAlive) b.Revive(player.transform.position + Vector3.back * 2f);
    }

    public void OnZombieKilled(ZombieAI z)
    {
        kills++;
        score += z.score;
        hud?.AnnounceSmall($"+{z.score}");
    }

    public void OnZombieHit(ZombieAI z) { /* hook for effects */ }

    public void FlashMuzzle()
    {
        if (muzzle == null) return;
        muzzle.SetActive(true);
        muzzleT = 0.06f;
    }

    public void Announce(string s) => hud?.Announce(s);

    void Update()
    {
        if (muzzleT > 0f)
        {
            muzzleT -= Time.deltaTime;
            if (muzzleT <= 0f && muzzle != null) muzzle.SetActive(false);
        }
        // global keys
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (Cursor.lockState == CursorLockMode.Locked)
            { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }
            else Application.Quit();
        }
        if (weapons != null)
        {
            if (Input.GetMouseButton(0)) weapons.Fire();
            if (Input.GetKeyDown(KeyCode.R)) weapons.Reload();
            if (Input.GetKeyDown(KeyCode.Q)) { weapons.Cycle(1); RefreshGunColor(); }
            for (int i = 0; i < 5; i++)
                if (Input.GetKeyDown((KeyCode)((int)KeyCode.Alpha1 + i))) { weapons.Switch(i); RefreshGunColor(); }
        }
        if (player != null && player.IsDead && !IsGameOver)
        {
            IsGameOver = true;
            Announce($"YOU DIED — Score {score} Kills {kills}");
        }
    }
}
