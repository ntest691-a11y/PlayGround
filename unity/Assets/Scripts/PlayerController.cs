using UnityEngine;

/// <summary>FPS controller: WASD + mouse look + gravity. Attached at runtime.</summary>
[RequireComponent(typeof(CharacterController))]
public class PlayerController : MonoBehaviour
{
    public float speed = 7f;
    public float mouseSens = 2.2f;
    public float hp = 100f;
    public float maxHp = 100f;

    private CharacterController cc;
    private float pitch = 0f;
    private float vy = 0f;

    public bool IsDead => hp <= 0f;

    void Awake()
    {
        cc = GetComponent<CharacterController>();
    }

    void Update()
    {
        if (hp <= 0f) return;
        // look
        float mx = Input.GetAxis("Mouse X") * mouseSens;
        float my = Input.GetAxis("Mouse Y") * mouseSens;
        transform.Rotate(0f, mx, 0f);
        pitch = Mathf.Clamp(pitch - my, -85f, 85f);
        var cam = GetComponentInChildren<Camera>();
        if (cam) cam.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        // move
        float h = Input.GetAxis("Horizontal");
        float v = Input.GetAxis("Vertical");
        Vector3 move = transform.right * h + transform.forward * v;
        move *= speed;
        if (cc.isGrounded) { if (vy < 0f) vy = -1f; }
        else vy += Physics.gravity.y * Time.deltaTime;
        move.y = vy;
        cc.Move(move * Time.deltaTime);
        // slow regen
        if (hp < maxHp) hp = Mathf.Min(maxHp, hp + 2f * Time.deltaTime);
    }

    public void Hurt(float amount)
    {
        if (hp <= 0f) return;
        hp -= amount;
    }
}
