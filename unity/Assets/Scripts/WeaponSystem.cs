using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>Weapon inventory + hitscan shooting. Data-driven from GameData.</summary>
public class WeaponSystem : MonoBehaviour
{
    public GameData data;
    public List<string> owned = new List<string>();
    public int current = 0;
    public Dictionary<string, int> mag = new Dictionary<string, int>();
    public Dictionary<string, int> reserve = new Dictionary<string, int>();
    public string forcedSkinId; // e.g. set "gold" to force skin on matching weapon
    public Transform muzzle;

    private float lastShot = -99f;
    private Camera cam;

    public string CurrentId => owned.Count == 0 ? null : owned[Mathf.Clamp(current, 0, owned.Count - 1)];
    public JObject CurrentDef() => CurrentId == null ? null : data.weapons[CurrentId];

    public void Setup(GameData data, Camera cam)
    {
        this.data = data;
        this.cam = cam;
        foreach (var wid in data.loadout) AddWeapon(wid);
    }

    public void AddWeapon(string wid)
    {
        if (!data.weapons.ContainsKey(wid) || owned.Contains(wid)) return;
        owned.Add(wid);
        var w = data.weapons[wid];
        mag[wid] = GameData.I(w, "magazine", 12);
        reserve[wid] = GameData.I(w, "reserve", 120);
    }

    public bool CanFire()
    {
        var w = CurrentDef();
        if (w == null || CurrentId == null) return false;
        if (mag[CurrentId] <= 0) return false;
        return Time.time - lastShot >= GameData.F(w, "fire_rate", 0.25f);
    }

    public void Reload()
    {
        var id = CurrentId;
        if (id == null) return;
        var w = CurrentDef();
        int size = GameData.I(w, "magazine", 12);
        int need = size - mag[id];
        int take = Mathf.Min(need, reserve[id]);
        mag[id] += take;
        reserve[id] -= take;
    }

    public void Cycle(int dir) { if (owned.Count > 0) current = (current + dir + owned.Count) % owned.Count; }
    public void Switch(int i) { if (i >= 0 && i < owned.Count) current = i; }

    /// Fire one trigger pull. Returns damage dealt (for HUD/score), 0 if none.
    public void Fire()
    {
        var id = CurrentId;
        var w = CurrentDef();
        if (id == null || w == null) return;
        if (mag[id] <= 0)
        {
            if (reserve[id] > 0) Reload();
            return;
        }
        if (Time.time - lastShot < GameData.F(w, "fire_rate", 0.25f)) return;
        lastShot = Time.time;
        mag[id]--;

        int pellets = GameData.I(w, "pellets", 1);
        float dmg = GameData.F(w, "damage", 20f);
        float range = GameData.F(w, "range", 60f);

        for (int p = 0; p < pellets; p++)
        {
            Vector3 dir = cam.transform.forward;
            // slight spread
            dir += cam.transform.right * Random.Range(-0.01f, 0.01f) + cam.transform.up * Random.Range(-0.01f, 0.01f);
            if (Physics.Raycast(cam.transform.position, dir.normalized, out RaycastHit hit, range))
            {
                var z = hit.collider.GetComponentInParent<ZombieAI>();
                if (z != null && z.IsAlive)
                {
                    bool head = hit.collider.name == "Head";
                    z.TakeDamage(head ? dmg * 1.5f : dmg);
                    GameBootstrap.Instance?.OnZombieHit(z);
                }
            }
        }
        if (muzzle != null) GameBootstrap.Instance?.FlashMuzzle();
    }
}
