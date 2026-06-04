import modal

app = modal.App("taco-mujoco")
img = (
    modal.Image.debian_slim()
    .apt_install("libegl1", "libgl1", "libglib2.0-0", "ffmpeg")
    .pip_install("mujoco", "imageio[ffmpeg]", "numpy")
    .env({"MUJOCO_GL": "egl", "NVIDIA_DRIVER_CAPABILITIES": "all"})
)

@app.function(gpu="A10G", image=img, timeout=300)
def smoke():
    import os
    os.environ["MUJOCO_GL"] = "egl"
    import mujoco, numpy as np, imageio.v2 as imageio, io
    xml = """<mujoco><visual><global offwidth='320' offheight='240'/></visual>
    <worldbody><light pos='0 0 2'/><geom type='plane' size='2 2 .1'/>
    <body pos='0 0 .5'><freejoint/><geom type='box' size='.12 .12 .12' rgba='.2 .5 .9 1'/></body>
    </worldbody></mujoco>"""
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    r = mujoco.Renderer(model, 240, 320)
    frames = []
    for _ in range(60):
        mujoco.mj_step(model, data)
        r.update_scene(data)
        frames.append(r.render())
    buf = io.BytesIO(); imageio.mimsave(buf, frames, format="mp4", fps=20)
    return buf.getvalue()

@app.local_entrypoint()
def main():
    data = smoke.remote()
    out = "taco_demo/data/videos/incoming/modal_mujoco_smoke.mp4"
    open(out, "wb").write(data)
    print(f"WROTE {out} ({len(data)} bytes)")
