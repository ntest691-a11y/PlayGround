using UnityEngine;

/// <summary>All HUD via OnGUI — zero editor setup needed.</summary>
public class GameHUD : MonoBehaviour
{
    private GameBootstrap gb;
    private string announce = "WAVE 1 — survive!";
    private string small = "";
    private float smallT = 0f;
    private bool showMods = false;
    private bool showHelp = false;
    private GUIStyle big;
    private GUIStyle label;

    public void Setup(GameBootstrap gb)
    {
        this.gb = gb;
        big = new GUIStyle(GUI.skin.label) { fontSize = 22, alignment = TextAnchor.MiddleCenter };
        label = new GUIStyle(GUI.skin.label) { fontSize = 15 };
    }

    public void Announce(string s) => announce = s;
    public void AnnounceSmall(string s) { small = s; smallT = 1.5f; }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.M)) showMods = !showMods;
        if (Input.GetKeyDown(KeyCode.F1)) showHelp = !showHelp;
        if (smallT > 0f) smallT -= Time.deltaTime;
    }

    void OnGUI()
    {
        if (gb == null) return;
        var w = gb.weapons;
        // crosshair
        GUI.Label(new Rect(Screen.width / 2 - 8, Screen.height / 2 - 14, 16, 28), "+", big);
        // top-left status
        string ammo = w != null && w.CurrentDef() != null
            ? $"{w.CurrentDef()["name"]}  {w.mag[w.CurrentId]}/{w.reserve[w.CurrentId]}" : "-";
        GUI.Label(new Rect(12, 10, 600, 24), $"HP {Mathf.Max(0, (int)gb.player.hp)}/100   {ammo}", label);
        GUI.Label(new Rect(12, 32, 600, 24),
            $"Wave {gb.waves.waveIndex + 1}   Kills {gb.kills}   Score {gb.score}   Zombies {gb.AliveZombies().Count}", label);
        // bots
        float y = 56f;
        foreach (var b in FindObjectsOfType<BuddyAI>())
            if (b.IsAlive) { GUI.Label(new Rect(12, y, 300, 22), $"{b.displayName}: {(int)b.hp}"); y += 22f; }
        // center announce
        GUI.Label(new Rect(0, 60, Screen.width, 30), announce, big);
        if (smallT > 0f) GUI.Label(new Rect(0, 92, Screen.width, 24), small, big);
        if (showHelp)
            GUI.Box(new Rect(Screen.width / 2 - 220, Screen.height / 2 - 60, 440, 120),
                "WASD move | Mouse look | LMB shoot | R reload | 1-4 weapons | Q cycle\nM mods | F1 help | Esc cursor/quit");
        if (showMods)
        {
            string list = "== MODS ==\n";
            foreach (var m in gb.loader.mods)
                list += $"[{(m.enabled ? "ON" : "off")}] {m.id} — {m.manifest.name}\n";
            GUI.Box(new Rect(12, 140, 420, 200), list);
        }
    }
}
