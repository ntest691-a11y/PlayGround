using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>Wave spawner: trickles zombies from spawn points, endless scaling.</summary>
public class WaveManager : MonoBehaviour
{
    public GameData data;
    public string mapId = "rooftop";
    public List<string> queue = new List<string>();
    public int waveIndex = 0;

    private float timer = 0f;
    private float retarget = 0f;

    public void Setup(GameData data, string mapId)
    {
        this.data = data;
        this.mapId = mapId;
        StartWave(0);
    }

    private JObject Map() => data.maps[mapId];

    private List<JObject> Waves()
    {
        var list = new List<JObject>();
        var arr = Map()["waves"] as JArray;
        if (arr != null) foreach (var w in arr) if (w is JObject jo) list.Add(jo);
        return list;
    }

    public void StartWave(int i)
    {
        waveIndex = i;
        queue.Clear();
        var waves = Waves();
        JObject w = i < waves.Count ? waves[i] : JObject.FromObject(new { count = 12 + i * 4 });
        int count = GameData.I(w, "count", 8);
        var types = new List<string>();
        var ta = w["types"] as JArray;
        if (ta != null) foreach (var t in ta) types.Add((string)t);
        if (types.Count == 0) types.AddRange(data.zombies.Keys);
        for (int k = 0; k < count; k++)
            queue.Add(types[Random.Range(0, types.Count)]);
        timer = 1f;
        GameBootstrap.Instance?.Announce($"WAVE {i + 1} — {count} infected!");
    }

    void Update()
    {
        var gb = GameBootstrap.Instance;
        if (gb == null || gb.IsGameOver) return;
        if (queue.Count > 0)
        {
            timer -= Time.deltaTime;
            if (timer <= 0f)
            {
                timer = 0.6f;
                string zid = queue[0];
                queue.RemoveAt(0);
                if (!data.zombies.ContainsKey(zid)) zid = "common";
                gb.SpawnZombie(zid);
            }
        }
        else if (gb.AliveZombies().Count == 0)
        {
            var waves = Waves();
            int next = waveIndex + 1;
            if (next >= waves.Count)
            {
                // endless: append generated wave into map def
                var arr = Map()["waves"] as JArray;
                var gen = new JObject { ["count"] = 12 + next * 4 };
                var all = new JArray();
                foreach (var z in data.zombies.Keys) all.Add(z);
                gen["types"] = all;
                arr.Add(gen);
            }
            gb.ClearCorpses();
            gb.ReviveBots();
            StartWave(next);
        }
        // retarget zombies to nearest target every 2s
        retarget -= Time.deltaTime;
        if (retarget <= 0f)
        {
            retarget = 2f;
            foreach (var z in gb.AliveZombies())
                z.target = gb.NearestTarget(z.transform.position);
        }
    }
}
