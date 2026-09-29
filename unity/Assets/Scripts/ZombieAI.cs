using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>Zombie: chases nearest target (player or bots), melee attack. Data-driven.</summary>
public class ZombieAI : MonoBehaviour
{
    public string zid = "common";
    public float hp = 100f;
    public float speed = 3.2f;
    public float damage = 12f;
    public float attackRange = 2f;
    public float attackRate = 1f;
    public int score = 100;

    public MonoBehaviour target; // PlayerController or BuddyAI
    public bool IsAlive => hp > 0f;

    private float cd = 0f;
    private float flashT = 0f;
    private Renderer bodyRenderer;
    private Color baseColor = Color.gray;

    public void Setup(string zid, JObject def, MonoBehaviour target)
    {
        this.zid = zid;
        this.target = target;
        hp = GameData.F(def, "hp", 100f);
        speed = GameData.F(def, "speed", 3f);
        damage = GameData.F(def, "damage", 10f);
        attackRange = GameData.F(def, "attack_range", 2f);
        attackRate = GameData.F(def, "attack_rate", 1f);
        score = GameData.I(def, "score", 100);
    }

    public void SetBody(Renderer r, Color baseColor)
    {
        bodyRenderer = r;
        this.baseColor = baseColor;
    }

    public Vector3 TargetPos()
    {
        if (target is PlayerController p) return p.transform.position;
        if (target is BuddyAI b) return b.transform.position;
        return transform.position;
    }

    void Update()
    {
        if (!IsAlive || target == null) return;
        Vector3 tp = TargetPos();
        Vector3 flat = new Vector3(tp.x - transform.position.x, 0f, tp.z - transform.position.z);
        float dist = flat.magnitude;
        if (dist > attackRange * 0.8f && dist > 0.01f)
            transform.position += flat.normalized * speed * Time.deltaTime;
        if (dist > 0.01f)
            transform.rotation = Quaternion.Slerp(transform.rotation,
                Quaternion.LookRotation(flat), 10f * Time.deltaTime);
        cd -= Time.deltaTime;
        if (dist <= attackRange && cd <= 0f)
        {
            cd = attackRate;
            if (target is PlayerController p) p.Hurt(damage);
            else if (target is BuddyAI b) b.Hurt(damage);
        }
    }

    public void TakeDamage(float amount)
    {
        if (!IsAlive) return;
        hp -= amount;
        if (bodyRenderer) { bodyRenderer.material.color = Color.white; flashT = 0.08f; }
        if (hp <= 0f)
        {
            hp = 0f;
            gameObject.SetActive(false);
            GameBootstrap.Instance?.OnZombieKilled(this);
        }
    }

    void LateUpdate()
    {
        // restore body color after hit flash
        if (flashT > 0f)
        {
            flashT -= Time.deltaTime;
            if (flashT <= 0f && bodyRenderer && IsAlive)
                bodyRenderer.material.color = baseColor;
        }
    }
}
