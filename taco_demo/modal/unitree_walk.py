"""Render natural humanoid walking videos using Unitree's OFFICIAL pretrained RL
locomotion policies (unitree_rl_gym) in plain MuJoCo, headless on Modal via EGL.

Success clip = the pretrained policy walks forward naturally (forward joystick cmd).
Fail clip    = same policy, but a large external push is applied mid-episode so the
               robot loses balance and falls (motion -> fall, not a static collapse).

Pretrained checkpoints used (repo paths):
  deploy/pre_train/g1/motion.pt   (12-DOF G1 legs, 47 obs)
  deploy/pre_train/h1/motion.pt   (10-DOF H1 legs, 41 obs)
Configs reused: deploy/deploy_mujoco/configs/{g1,h1}.yaml
Scene XMLs:     resources/robots/{g1_description,h1}/scene.xml
"""
import modal

app = modal.App("taco-unitree-walk")

REPO = "https://github.com/unitreerobotics/unitree_rl_gym"

img = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libegl1", "libgl1", "libglib2.0-0", "ffmpeg", "git")
    .pip_install("mujoco==3.2.7", "imageio[ffmpeg]", "numpy", "torch", "pyyaml")
    .run_commands(f"git clone --depth 1 {REPO} /unitree_rl_gym")
    .env({"MUJOCO_GL": "egl", "NVIDIA_DRIVER_CAPABILITIES": "all"})
)

ROOT = "/unitree_rl_gym"


def _get_gravity_orientation(quaternion):
    import numpy as np
    qw, qx, qy, qz = quaternion
    g = np.zeros(3)
    g[0] = 2 * (-qz * qx + qw * qy)
    g[1] = -2 * (qz * qy + qw * qx)
    g[2] = 1 - 2 * (qw * qw + qz * qz)
    return g


def _pd_control(target_q, q, kp, target_dq, dq, kd):
    return (target_q - q) * kp + (target_dq - dq) * kd


# Per-robot torso shove (N) used for the fail clip. H1 is much heavier than G1,
# so it needs a substantially larger force to lose balance.
PUSH_FORCE = {
    "g1": (60.0, 180.0, 0.0),
    "h1": (260.0, 700.0, 80.0),
    "h1_2": (260.0, 700.0, 80.0),
}


@app.function(gpu="A10G", image=img, timeout=900)
def render(robot: str = "g1", mode: str = "success", steps: int = 450):
    """Run the pretrained Unitree sim2sim deploy headless and return mp4 bytes.

    mode == "success": forward walk command, no disturbance.
    mode == "fail":    forward walk, then a strong lateral+forward shove to the
                       torso partway through so the policy loses balance and falls.
    """
    import os, io, yaml, numpy as np, imageio.v2 as imageio, mujoco, torch
    os.environ["MUJOCO_GL"] = "egl"

    cfg_path = f"{ROOT}/deploy/deploy_mujoco/configs/{robot}.yaml"
    with open(cfg_path) as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    policy_path = cfg["policy_path"].replace("{LEGGED_GYM_ROOT_DIR}", ROOT)
    xml_path = cfg["xml_path"].replace("{LEGGED_GYM_ROOT_DIR}", ROOT)

    sim_dt = cfg["simulation_dt"]
    control_decimation = cfg["control_decimation"]
    kps = np.array(cfg["kps"], dtype=np.float32)
    kds = np.array(cfg["kds"], dtype=np.float32)
    default_angles = np.array(cfg["default_angles"], dtype=np.float32)
    ang_vel_scale = cfg["ang_vel_scale"]
    dof_pos_scale = cfg["dof_pos_scale"]
    dof_vel_scale = cfg["dof_vel_scale"]
    action_scale = cfg["action_scale"]
    cmd_scale = np.array(cfg["cmd_scale"], dtype=np.float32)
    num_actions = cfg["num_actions"]
    num_obs = cfg["num_obs"]
    cmd = np.array(cfg["cmd_init"], dtype=np.float32)  # forward joystick command

    action = np.zeros(num_actions, dtype=np.float32)
    target_dof_pos = default_angles.copy()
    obs = np.zeros(num_obs, dtype=np.float32)

    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    m.opt.timestep = sim_dt
    policy = torch.jit.load(policy_path)

    # torso/free-joint body for applying the disturbance (body index 1 = base)
    base_body = 1

    renderer = mujoco.Renderer(m, 480, 640)
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.distance = 3.5
    cam.elevation = -18
    cam.azimuth = 120

    frames = []
    counter = 0
    # control steps -> total sim steps
    total_steps = steps * control_decimation
    # for the fail clip, shove early (after a few steps of walking) so the robot
    # is down for most of the clip -> obvious contrast with the success walk.
    push_start = int(total_steps * 0.18)
    push_end = push_start + 180  # ~0.36s of sustained shove
    push_vec = np.array(PUSH_FORCE.get(robot, (60.0, 180.0, 0.0)), dtype=np.float64)

    for i in range(total_steps):
        tau = _pd_control(target_dof_pos, d.qpos[7:], kps,
                          np.zeros_like(kds), d.qvel[6:], kds)
        d.ctrl[:] = tau

        if mode == "fail" and push_start <= i < push_end:
            # strong external force on the torso (lateral + forward + slight up)
            # to topple the robot while it is mid-stride.
            d.xfrc_applied[base_body, :3] = push_vec
        else:
            d.xfrc_applied[base_body, :3] = 0.0

        mujoco.mj_step(m, d)
        counter += 1

        if counter % control_decimation == 0:
            qj = d.qpos[7:]
            dqj = d.qvel[6:]
            quat = d.qpos[3:7]
            omega = d.qvel[3:6]

            qj = (qj - default_angles) * dof_pos_scale
            dqj = dqj * dof_vel_scale
            gravity_orientation = _get_gravity_orientation(quat)
            omega = omega * ang_vel_scale

            period = 0.8
            count = counter * sim_dt
            phase = count % period / period
            sin_phase = np.sin(2 * np.pi * phase)
            cos_phase = np.cos(2 * np.pi * phase)

            obs[:3] = omega
            obs[3:6] = gravity_orientation
            obs[6:9] = cmd * cmd_scale
            obs[9:9 + num_actions] = qj
            obs[9 + num_actions:9 + 2 * num_actions] = dqj
            obs[9 + 2 * num_actions:9 + 3 * num_actions] = action
            obs[9 + 3 * num_actions:9 + 3 * num_actions + 2] = np.array([sin_phase, cos_phase])
            obs_tensor = torch.from_numpy(obs).unsqueeze(0)
            action = policy(obs_tensor).detach().numpy().squeeze()
            target_dof_pos = action * action_scale + default_angles

            # camera tracks the robot's base position so it stays centered
            cam.lookat[:] = d.qpos[:3]
            renderer.update_scene(d, cam)
            frames.append(renderer.render())

    buf = io.BytesIO()
    imageio.mimsave(buf, frames, format="mp4", fps=30)
    return buf.getvalue()


@app.local_entrypoint()
def one(robot: str = "h1", mode: str = "fail", steps: int = 450):
    import os
    incoming = "taco_demo/data/videos/incoming/unitree_walk"
    landing = "landing/public/videos"
    os.makedirs(incoming, exist_ok=True)
    data = render.remote(robot=robot, mode=mode, steps=steps)
    name = f"{robot}_walk_{mode}.mp4"
    for dd in (incoming, landing):
        p = os.path.join(dd, name)
        open(p, "wb").write(data)
        print(f"WROTE {p} ({len(data)} bytes)")


@app.local_entrypoint()
def main(robots: str = "g1,h1", steps: int = 450):
    import os
    incoming = "taco_demo/data/videos/incoming/unitree_walk"
    landing = "landing/public/videos"
    os.makedirs(incoming, exist_ok=True)
    os.makedirs(landing, exist_ok=True)

    jobs = []
    for robot in robots.split(","):
        robot = robot.strip()
        for mode in ("success", "fail"):
            jobs.append((robot, mode))

    handles = {(r, mode): render.spawn(robot=r, mode=mode, steps=steps)
               for (r, mode) in jobs}

    for (r, mode), h in handles.items():
        data = h.get()
        name = f"{r}_walk_{'success' if mode == 'success' else 'fail'}.mp4"
        for d in (incoming, landing):
            p = os.path.join(d, name)
            open(p, "wb").write(data)
            print(f"WROTE {p} ({len(data)} bytes)")
