using UnityEngine;

/// <summary>Survivor bot: follows the player, auto-shoots nearest zombie.</summary>
public class BuddyAI : MonoBehaviour
{
    public string displayName = "Doc";
    public float hp = 100f;
    public float maxHp = 100f;
    public bool IsAlive => hp > 0f;

    private Transform player;
    private float side;
    private float cd = 0f;

    public void Setup(string name, Transform player, float side)
    {
        displayName = name;
        this.player = player;
        this.side = side;
    }

    public void Hurt(float amount)
    {
        if (!IsAlive) return;
        hp -= amount;
        if (hp <= 0f) { hp = 0f; gameObject.SetActive(false); }
    }

    public void Revive(Vector3 near)
    {
        hp = 60f;
        transform.position = near;
        gameObject.SetActive(true);
    }

    void Update()
    {
        if (!IsAlive || player == null) return;
        Vector3 fwd = player.forward;
        fwd.y = 0f;
        if (fwd.sqrMagnitude < 0.01f) fwd = Vector3.forward;
        fwd.Normalize();
        Vector3 right = new Vector3(fwd.z, 0f, -fwd.x);
        Vector3 want = player.position - fwd * 2.5f + right * (1.5f * side);
        want.y = player.position.y;
        Vector3 diff = want - transform.position;
        if (diff.magnitude > 0.3f)
            transform.position += diff.normalized * Mathf.Min(diff.magnitude, 6.5f * Time.deltaTime);

        // shoot nearest zombie in 35m
        ZombieAI best = null;
        float bd = 35f;
        foreach (var z in GameBootstrap.Instance.AliveZombies())
        {
            float d = Vector3.Distance(z.transform.position, transform.position);
            if (d < bd) { bd = d; best = z; }
        }
        if (best != null)
        {
            Vector3 flat = best.transform.position - transform.position;
            flat.y = 0f;
            if (flat.sqrMagnitude > 0.01f)
                transform.rotation = Quaternion.LookRotation(flat);
            cd -= Time.deltaTime;
            if (cd <= 0f) { cd = 0.7f; best.TakeDamage(14f); }
        }
    }
}
