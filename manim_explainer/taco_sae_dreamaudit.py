"""ManimGL explainer for TACO's SAE + DreamAudit interpretability story.

Render:
    .venv/bin/manimgl manim_explainer/taco_sae_dreamaudit.py TacoSAEDreamAuditExplainer -w

This uses the 3b1b ManimGL API (`from manimlib import *`). It avoids LaTeX so
the first render is mostly an OpenGL/FFmpeg dependency check.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

try:
    from manimlib import *
except ModuleNotFoundError:  # pragma: no cover - lets the data smoke check run without ManimGL.
    MANIM_AVAILABLE = False
else:
    MANIM_AVAILABLE = True


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FALLBACK = {
    "d_model": 256,
    "d_sae": 4096,
    "expansion": 16,
    "alive_features": 1172,
    "explained_variance": 0.998,
    "l0": 64,
    "n_samples": 1976,
    "first_alert_step": 32,
    "action_alert_step": 56,
    "failure_step": 80,
    "lead_steps": 48,
    "recall": 1.0,
    "precision": 0.857,
    "false_alert_count": 1,
}


def load_taco_numbers() -> dict[str, float | int | str]:
    """Load real local TACO artifact summaries, with a documented fallback."""
    numbers = dict(FALLBACK)
    try:
        from taco_demo.external_evidence import fr004_certificate, saescope_summary
        from taco_demo.sae_features import sae_overview

        sae = sae_overview()
        summary = saescope_summary()
        cert = fr004_certificate()
    except Exception:
        numbers["source"] = "fallback documented values"
        return numbers

    numbers.update(
        {
            "d_model": int(sae.get("d_model") or numbers["d_model"]),
            "d_sae": int(sae.get("d_sae") or numbers["d_sae"]),
            "expansion": int(sae.get("expansion") or numbers["expansion"]),
            "alive_features": int(sae.get("alive_features") or numbers["alive_features"]),
            "explained_variance": float(sae.get("explained_variance") or numbers["explained_variance"]),
            "l0": int(round(float(sae.get("l0") or numbers["l0"]))),
            "n_samples": int(sae.get("n_samples") or numbers["n_samples"]),
            "first_alert_step": int(summary.get("first_alert_step") or numbers["first_alert_step"]),
            "lead_steps": int(round(float(summary.get("mean_early_warning_lead_steps") or numbers["lead_steps"]))),
            "recall": float(summary.get("recall") or numbers["recall"]),
            "precision": float(summary.get("precision") or numbers["precision"]),
            "false_alert_count": int(summary.get("false_alert_count") or numbers["false_alert_count"]),
            "policy": str(summary.get("policy") or "VLA diffusion policy"),
            "environment": str(summary.get("environment") or "SimplerEnv move_near"),
            "certificate": str(cert.get("certificate_id") or "FR-004"),
            "control": str(cert.get("recommended_control") or "internal_risk_monitor_handoff_on_alert"),
            "source": "local TACO artifacts",
        }
    )
    numbers["failure_step"] = int(numbers["first_alert_step"]) + int(numbers["lead_steps"])
    return numbers


if not MANIM_AVAILABLE:
    if __name__ == "__main__":
        print(load_taco_numbers())
    else:
        raise ModuleNotFoundError("Install ManimGL with `pip install manimgl` to render this scene.")


if MANIM_AVAILABLE:
    BG = "#101216"
    PANEL = "#171b22"
    PANEL_2 = "#202633"
    INK = "#f7f7f2"
    MUTED = "#a9b0bd"
    BLUE_ACCENT = "#4cc9f0"
    GREEN_ACCENT = "#7bd88f"
    YELLOW_ACCENT = "#ffd166"
    RED_ACCENT = "#ff5c5c"
    PURPLE_ACCENT = "#b88cff"
    PLAY_SLOWDOWN = 1.45
    WAIT_SLOWDOWN = 1.65


    def txt(value: str, size: int = 30, color: str = INK, weight: str = "REGULAR"):
        return Text(value, font_size=size, color=color, weight=weight)


    def panel(width: float, height: float, color: str = PANEL):
        box = Rectangle(width=width, height=height)
        box.set_fill(color, opacity=1)
        box.set_stroke("#3a4250", width=1.5)
        return box


    def metric_card(label: str, value: str, width: float = 2.25, accent: str = BLUE_ACCENT):
        bg = panel(width, 1.0, PANEL_2)
        top = Rectangle(width=width, height=0.08)
        top.set_fill(accent, opacity=1)
        top.set_stroke(accent, width=0)
        top.next_to(bg.get_top(), DOWN, buff=0)
        name = txt(label, 18, MUTED)
        num = txt(value, 28, INK, "BOLD")
        if name.get_width() > width - 0.2:
            name.set_width(width - 0.2)
        if num.get_width() > width - 0.2:
            num.set_width(width - 0.2)
        name.next_to(bg.get_top(), DOWN, buff=0.18)
        num.next_to(name, DOWN, buff=0.08)
        return VGroup(bg, top, name, num)


    def small_label(value: str, mob, direction=DOWN, buff: float = 0.12, color: str = MUTED, size: int = 18):
        label = txt(value, size, color)
        label.next_to(mob, direction, buff=buff)
        return label


    def vector_lights(rows: int, cols: int, active: set[int], cell: float = 0.16):
        dots = VGroup()
        for i in range(rows * cols):
            dot = Circle(radius=cell * 0.42)
            if i in active:
                colors = [BLUE_ACCENT, YELLOW_ACCENT, PURPLE_ACCENT, GREEN_ACCENT]
                dot.set_fill(colors[i % len(colors)], opacity=0.95)
                dot.set_stroke(WHITE, width=0.5, opacity=0.5)
            else:
                dot.set_fill("#303743", opacity=0.9)
                dot.set_stroke("#3b4452", width=0.4)
            r = i // cols
            c = i % cols
            dot.move_to(np.array([c * cell, -r * cell, 0.0]))
            dots.add(dot)
        dots.center()
        return dots


    def sparse_bars(count: int = 32, hot: tuple[int, ...] = (4, 11, 18, 25)):
        bars = VGroup()
        for i in range(count):
            h = 0.22 + 0.08 * ((i * 7) % 5)
            color = "#313947"
            opacity = 0.85
            if i in hot:
                h = [1.1, 0.8, 1.35, 0.95][hot.index(i)]
                color = [GREEN_ACCENT, BLUE_ACCENT, YELLOW_ACCENT, PURPLE_ACCENT][hot.index(i)]
                opacity = 1
            rect = Rectangle(width=0.08, height=h)
            rect.set_fill(color, opacity=opacity)
            rect.set_stroke(color, width=0)
            rect.move_to(np.array([i * 0.13, h / 2, 0.0]))
            bars.add(rect)
        bars.center()
        return bars


    def curve_from_points(points: list[tuple[float, float]], width: float, height: float, color: str):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = 0.0, max(1.0, max(ys))

        def project(x: float, y: float):
            px = -width / 2 + width * (x - min_x) / max(max_x - min_x, 1e-6)
            py = -height / 2 + height * (y - min_y) / max(max_y - min_y, 1e-6)
            return np.array([px, py, 0.0])

        mob = VMobject()
        mob.set_points_as_corners([project(x, y) for x, y in points])
        mob.set_stroke(color, width=4)
        return mob


    def timeline_marker(step: int, max_step: int, width: float, height: float, color: str, label: str):
        x = -width / 2 + width * step / max_step
        line = Line(np.array([x, -height / 2, 0.0]), np.array([x, height / 2, 0.0]))
        line.set_stroke(color, width=2)
        tag = txt(label, 16, color, "BOLD")
        tag.next_to(line, UP, buff=0.08)
        return VGroup(line, tag)


    def node_column(count: int, radius: float = 0.13, active: set[int] | None = None, color: str = BLUE_ACCENT):
        active = active or set()
        nodes = VGroup()
        for i in range(count):
            dot = Circle(radius=radius)
            dot.set_stroke(WHITE, width=1.2, opacity=0.85)
            fill = color if i in active else "#555b64"
            dot.set_fill(fill, opacity=0.9 if i in active else 0.45)
            dot.shift(UP * ((count - 1) / 2 - i) * radius * 3.0)
            nodes.add(dot)
        return nodes


    def connect_layers(left, right, color: str = "#6d7480", width: float = 1.0, opacity: float = 0.35):
        lines = VGroup()
        for a in left:
            for b in right:
                line = Line(a.get_center(), b.get_center())
                line.set_stroke(color, width=width, opacity=opacity)
                lines.add(line)
        return lines


    def bar_chart(labels: list[str], values: list[float], width: float = 4.3, height: float = 2.1, hot: set[int] | None = None):
        hot = hot or set()
        bars = VGroup()
        max_val = max(max(values), 1e-6)
        gap = width / max(len(values), 1)
        for i, value in enumerate(values):
            bar_h = height * value / max_val
            rect = Rectangle(width=gap * 0.55, height=max(bar_h, 0.04))
            color = [BLUE_ACCENT, GREEN_ACCENT, YELLOW_ACCENT, PURPLE_ACCENT, RED_ACCENT][i % 5]
            rect.set_fill(color if i in hot else "#3a4250", opacity=0.95 if i in hot else 0.55)
            rect.set_stroke(color if i in hot else "#4b5563", width=1)
            rect.move_to(np.array([-width / 2 + gap * (i + 0.5), -height / 2 + bar_h / 2, 0.0]))
            label = txt(labels[i], 13, color if i in hot else MUTED)
            label.next_to(rect, DOWN, buff=0.08)
            bars.add(VGroup(rect, label))
        return bars


    def formula_line(parts: list[tuple[str, str]], size: int = 30):
        group = VGroup(*[txt(text, size, color, "BOLD" if color != MUTED else "REGULAR") for text, color in parts])
        group.arrange(RIGHT, buff=0.08)
        return group


    class TacoSAEDreamAuditExplainer(Scene):
        def setup(self):
            self.camera.background_color = BG
            self.numbers = load_taco_numbers()

        def play(self, *animations, **kwargs):
            kwargs["run_time"] = float(kwargs.get("run_time", 1.0)) * PLAY_SLOWDOWN
            return super().play(*animations, **kwargs)

        def wait(self, duration: float = 1.0, *args, **kwargs):
            return super().wait(duration * WAIT_SLOWDOWN, *args, **kwargs)

        def construct(self):
            self.opening()
            self.activation_vocabulary()
            self.what_is_a_feature()
            self.superposition_problem()
            self.sae_mechanics()
            self.topk_definition()
            self.monitor_definition()
            self.black_box_to_activations()
            self.sae_prism()
            self.general_vs_memorized()
            self.dreamaudit_timeline()
            self.certification_translation()
            self.final_frame()

        def title(self, value: str, subtitle: str | None = None):
            heading = txt(value, 42, INK, "BOLD")
            if heading.get_width() > 12.0:
                heading.set_width(12.0)
            heading.to_edge(UP, buff=0.35)
            if subtitle:
                sub = txt(subtitle, 22, MUTED)
                if sub.get_width() > 11.2:
                    sub.set_width(11.2)
                sub.next_to(heading, DOWN, buff=0.12)
                return VGroup(heading, sub)
            return VGroup(heading)

        def opening(self):
            title = self.title(
                "What TACO sees inside a robot failure",
                "Sparse features + replayable perturbations become certification evidence",
            )
            cards = VGroup(
                metric_card("SAE expansion", f"{self.numbers['d_model']} -> {self.numbers['d_sae']}", accent=BLUE_ACCENT),
                metric_card("Median active", f"{self.numbers['l0']} features", accent=GREEN_ACCENT),
                metric_card("FR-004 lead", f"{self.numbers['lead_steps']} steps", accent=YELLOW_ACCENT),
                metric_card("Monitor precision", f"{self.numbers['precision']:.3f}", accent=PURPLE_ACCENT),
            )
            cards.arrange(RIGHT, buff=0.22)
            cards.next_to(title, DOWN, buff=0.8)
            source = txt(f"Numbers loaded from {self.numbers['source']}", 18, MUTED)
            source.next_to(cards, DOWN, buff=0.35)

            self.play(FadeIn(title, shift=DOWN), run_time=1.0)
            self.play(*[FadeIn(card, shift=UP) for card in cards], run_time=1.2)
            self.play(FadeIn(source), run_time=0.5)
            self.wait(1.5)
            self.play(FadeOut(VGroup(title, cards, source)))

        def activation_vocabulary(self):
            title = self.title(
                "First: what is the model's internal state?",
                "A neural net is not just an action machine; it is a stream of numbers.",
            )

            pixels = VGroup()
            for r in range(7):
                for c in range(7):
                    sq = Square(side_length=0.18)
                    bright = 0.2 + 0.75 * math.exp(-((r - 2.5) ** 2 + (c - 3.2) ** 2) / 5.0)
                    sq.set_fill(interpolate_color("#242a35", BLUE_ACCENT, bright), opacity=1)
                    sq.set_stroke("#3a4250", width=0.5)
                    sq.move_to(np.array([c * 0.19, -r * 0.19, 0.0]))
                    pixels.add(sq)
            pixels.center().shift(LEFT * 5.1 + UP * 0.15)
            pixel_label = txt("pixels", 20, MUTED).next_to(pixels, DOWN, buff=0.2)

            instruction = panel(2.1, 0.65, "#182026").shift(LEFT * 5.1 + DOWN * 1.75)
            instruction_text = txt('"move near orange"', 18, INK).move_to(instruction)
            input_group = VGroup(pixels, pixel_label, instruction, instruction_text)

            layer1 = node_column(6, radius=0.12, active={1, 3, 4}, color=BLUE_ACCENT).shift(LEFT * 2.7)
            layer2 = node_column(5, radius=0.14, active={0, 2, 3}, color=GREEN_ACCENT).shift(LEFT * 0.75)
            layer3 = node_column(4, radius=0.14, active={1, 2}, color=YELLOW_ACCENT).shift(RIGHT * 1.1)
            conns = VGroup(
                connect_layers(layer1, layer2, opacity=0.22),
                connect_layers(layer2, layer3, opacity=0.25),
            )
            net = VGroup(conns, layer1, layer2, layer3)

            neuron = layer2[2].copy()
            neuron.scale(1.65)
            neuron.set_stroke(YELLOW_ACCENT, width=2.5)
            neuron_label = txt("neuron", 22, YELLOW_ACCENT, "BOLD").next_to(layer2, UP, buff=0.18)
            weight_lines = VGroup()
            for node in layer1:
                line = Line(node.get_center(), layer2[2].get_center())
                line.set_stroke(GREEN_ACCENT if node in [layer1[1], layer1[3], layer1[4]] else RED_ACCENT, width=2, opacity=0.8)
                weight_lines.add(line)
            weight_label = txt("weights say how much each input matters", 19, GREEN_ACCENT)
            weight_label.next_to(weight_lines, DOWN, buff=0.35)

            formula = txt("activation = weighted sum + bias, then nonlinearity", 25, INK, "BOLD")
            formula.to_edge(DOWN, buff=0.55)

            hidden_vec = vector_lights(4, 8, {2, 5, 9, 13, 17, 21, 30}, cell=0.16)
            hidden_vec.shift(RIGHT * 4.7 + UP * 0.35)
            h_label = txt("activation vector h", 24, BLUE_ACCENT, "BOLD").next_to(hidden_vec, UP, buff=0.22)
            h_sub = txt("a snapshot of what the model is representing now", 19, MUTED)
            h_sub.set_width(3.1)
            h_sub.next_to(hidden_vec, DOWN, buff=0.2)

            arrow_in = Arrow(input_group.get_right(), layer1.get_left(), buff=0.2).set_stroke(MUTED, 2.5)
            arrow_out = Arrow(layer3.get_right(), hidden_vec.get_left(), buff=0.2).set_stroke(MUTED, 2.5)

            self.play(FadeIn(title))
            self.play(FadeIn(input_group, shift=RIGHT), ShowCreation(arrow_in), FadeIn(net), run_time=1.2)
            self.play(ShowCreation(weight_lines), FadeIn(neuron), FadeIn(neuron_label), FadeIn(weight_label), run_time=1.0)
            self.play(FadeIn(formula, shift=UP), run_time=0.6)
            self.play(ShowCreation(arrow_out), FadeIn(hidden_vec, shift=RIGHT), FadeIn(h_label), FadeIn(h_sub), run_time=1.0)
            self.wait(1.6)
            self.play(FadeOut(VGroup(title, input_group, arrow_in, net, weight_lines, neuron, neuron_label, weight_label, formula, arrow_out, hidden_vec, h_label, h_sub)))

        def what_is_a_feature(self):
            title = self.title(
                "A feature is a direction, not necessarily one neuron",
                "Think of the activation vector as a point in a high-dimensional space.",
            )

            plane = NumberPlane(
                x_range=(-3, 3, 1),
                y_range=(-2, 2, 1),
                width=5.05,
                height=3.55,
            )
            plane.set_stroke("#3a4250", width=1, opacity=0.7)
            plane.shift(LEFT * 3.35 + DOWN * 0.2)
            x_axis = txt("neuron 1", 17, MUTED).next_to(plane, DOWN, buff=0.1)
            y_axis = txt("neuron 2", 17, MUTED).next_to(plane, LEFT, buff=0.1)

            origin = plane.c2p(0, 0)
            h_point = Dot(plane.c2p(1.9, 0.95), radius=0.08).set_fill(INK, 1)
            h_label = txt("h", 28, INK, "BOLD").next_to(h_point, UR, buff=0.08)
            feature_vec = Arrow(origin, plane.c2p(2.25, 1.45), buff=0)
            feature_vec.set_stroke(GREEN_ACCENT, width=5)
            feature_label = txt("feature direction d", 23, GREEN_ACCENT, "BOLD")
            feature_label.set_width(2.4)
            feature_label.move_to(feature_vec.get_end() + UP * 0.35 + LEFT * 0.1)

            projection = Line(h_point.get_center(), plane.c2p(1.55, 1.0))
            projection.set_stroke(YELLOW_ACCENT, width=3, opacity=0.9)
            proj_dot = Dot(plane.c2p(1.55, 1.0), radius=0.065).set_fill(YELLOW_ACCENT, 1)

            definition = panel(4.25, 3.25, "#171b22").shift(RIGHT * 3.55 + DOWN * 0.25)
            heading = txt("definition", 25, INK, "BOLD").next_to(definition.get_top(), DOWN, buff=0.22)
            bullets = VGroup(
                txt("feature: reusable activation pattern", 18, GREEN_ACCENT),
                txt("activation: how strongly h points that way", 18, YELLOW_ACCENT),
                txt("human label: our best description", 18, INK),
                txt("example: gripper closing near object", 18, INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            bullets.move_to(definition.get_center() + DOWN * 0.15)
            formula = txt("z_i = feature score ~= h dot d_i", 24, INK, "BOLD")
            formula.next_to(definition, DOWN, buff=0.24)

            self.play(FadeIn(title), FadeIn(plane), FadeIn(x_axis), FadeIn(y_axis))
            self.play(FadeIn(h_point), FadeIn(h_label), ShowCreation(feature_vec), FadeIn(feature_label), run_time=1.0)
            self.play(ShowCreation(projection), FadeIn(proj_dot), run_time=0.8)
            self.play(FadeIn(definition, shift=LEFT), FadeIn(heading), FadeIn(bullets, shift=UP), FadeIn(formula), run_time=1.1)
            self.wait(1.9)
            self.play(FadeOut(VGroup(title, plane, x_axis, y_axis, h_point, h_label, feature_vec, feature_label, projection, proj_dot, definition, heading, bullets, formula)))

        def superposition_problem(self):
            title = self.title(
                "Why not just inspect neurons directly?",
                "Models often pack more useful concepts than they have clean coordinates.",
            )

            left = panel(4.8, 3.55, "#171b22").shift(LEFT * 2.75 + DOWN * 0.15)
            right = panel(4.8, 3.55, "#171b22").shift(RIGHT * 2.75 + DOWN * 0.15)
            left_title = txt("what we want", 25, GREEN_ACCENT, "BOLD").next_to(left, UP, buff=0.16)
            right_title = txt("what the network stores", 25, YELLOW_ACCENT, "BOLD").next_to(right, UP, buff=0.16)

            concepts = VGroup(
                txt("object is close", 21, BLUE_ACCENT),
                txt("gripper should close", 21, GREEN_ACCENT),
                txt("language target = orange", 21, YELLOW_ACCENT),
                txt("episode-specific shortcut", 21, PURPLE_ACCENT),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            concepts.move_to(left.get_center())

            axes = NumberPlane(x_range=(-2.3, 2.3, 1), y_range=(-1.6, 1.6, 1), width=3.7, height=2.6)
            axes.set_stroke("#3a4250", width=1, opacity=0.65)
            axes.move_to(right.get_center() + UP * 0.18)
            origin = axes.c2p(0, 0)
            vectors = VGroup()
            vec_specs = [
                (2.0, 0.2, BLUE_ACCENT, "close"),
                (1.2, 1.2, GREEN_ACCENT, "close gripper"),
                (-0.1, 1.45, YELLOW_ACCENT, "orange"),
                (-1.25, 0.8, PURPLE_ACCENT, "shortcut"),
            ]
            labels = VGroup()
            for x, y, color, label in vec_specs:
                arr = Arrow(origin, axes.c2p(x, y), buff=0).set_stroke(color, width=3.5)
                lab = txt(label, 15, color).next_to(arr.get_end(), UP if y > 0.9 else RIGHT, buff=0.06)
                vectors.add(arr)
                labels.add(lab)
            neuron_note = txt("four feature directions squeezed into two drawn coordinates", 18, MUTED)
            neuron_note.set_width(4.0)
            neuron_note.next_to(axes, DOWN, buff=0.25)

            mix = VGroup(
                txt("polysemantic neuron", 24, RED_ACCENT, "BOLD"),
                txt("one coordinate can help represent many different features", 20, INK),
            ).arrange(DOWN, buff=0.12)
            mix.set_width(6.4)
            mix.to_edge(DOWN, buff=0.45)

            arrows = VGroup()
            for concept, vec in zip(concepts, vectors):
                arr = Arrow(concept.get_right(), vec.get_start(), buff=0.15)
                arr.set_stroke("#586171", width=1.7, opacity=0.45)
                arrows.add(arr)

            self.play(FadeIn(title), FadeIn(left), FadeIn(right), FadeIn(left_title), FadeIn(right_title))
            self.play(FadeIn(concepts, shift=RIGHT), run_time=0.8)
            self.play(FadeIn(axes), *[ShowCreation(v) for v in vectors], FadeIn(labels), run_time=1.2)
            self.play(*[ShowCreation(a) for a in arrows], FadeIn(neuron_note), FadeIn(mix, shift=UP), run_time=1.0)
            self.wait(1.7)
            self.play(FadeOut(VGroup(title, left, right, left_title, right_title, concepts, axes, vectors, labels, neuron_note, mix, arrows)))

        def sae_mechanics(self):
            title = self.title(
                "Sparse autoencoder: learn a new coordinate system",
                "Encode h into sparse features z, then decode z back into h_hat.",
            )

            dense = vector_lights(5, 7, {1, 4, 8, 9, 15, 19, 22, 28, 31}, cell=0.17)
            dense.shift(LEFT * 5.1 + UP * 0.35)
            dense_label = txt("original activation h", 22, BLUE_ACCENT, "BOLD").next_to(dense, DOWN, buff=0.2)

            encoder = panel(1.75, 1.15, "#213049").shift(LEFT * 2.6 + UP * 0.35)
            enc_text = txt("encoder", 24, INK, "BOLD").move_to(encoder)
            score_text = txt("feature scores", 17, MUTED).next_to(encoder, UP, buff=0.15)

            bars = sparse_bars(30, hot=(3, 8, 17, 24))
            bars.scale(1.05)
            bars.shift(UP * 0.1)
            z_label = txt("sparse feature vector z", 22, YELLOW_ACCENT, "BOLD").next_to(bars, DOWN, buff=0.25)

            decoder = panel(1.75, 1.15, "#243322").shift(RIGHT * 2.6 + UP * 0.35)
            dec_text = txt("decoder", 24, INK, "BOLD").move_to(decoder)
            dict_text = txt("dictionary vectors d_i", 17, MUTED).next_to(decoder, UP, buff=0.15)

            recon = vector_lights(5, 7, {1, 4, 8, 9, 15, 19, 22, 28, 31}, cell=0.17)
            recon.shift(RIGHT * 5.1 + UP * 0.35)
            recon_label = txt("reconstruction h_hat", 20, GREEN_ACCENT, "BOLD").next_to(recon, DOWN, buff=0.2)
            if recon_label.get_width() > 2.55:
                recon_label.set_width(2.55)

            arrows = VGroup(
                Arrow(dense.get_right(), encoder.get_left(), buff=0.15),
                Arrow(encoder.get_right(), bars.get_left(), buff=0.15),
                Arrow(bars.get_right(), decoder.get_left(), buff=0.15),
                Arrow(decoder.get_right(), recon.get_left(), buff=0.15),
            )
            arrows.set_stroke(MUTED, width=2.5)

            objective = panel(8.6, 1.45, "#161b23").to_edge(DOWN, buff=0.35)
            formula = txt("training goal: h_hat close to h, z stays sparse", 24, INK, "BOLD")
            formula.move_to(objective.get_center() + UP * 0.23)
            reconstruct = txt("h_hat = z_3 d_3 + z_8 d_8 + z_17 d_17 + ...", 24, INK, "BOLD")
            reconstruct.move_to(objective.get_center() + DOWN * 0.28)

            self.play(FadeIn(title))
            self.play(FadeIn(dense), FadeIn(dense_label), run_time=0.7)
            self.play(ShowCreation(arrows[0]), FadeIn(encoder), FadeIn(enc_text), FadeIn(score_text), run_time=0.7)
            self.play(ShowCreation(arrows[1]), FadeIn(bars, shift=RIGHT), FadeIn(z_label), run_time=0.9)
            self.play(ShowCreation(arrows[2]), FadeIn(decoder), FadeIn(dec_text), FadeIn(dict_text), run_time=0.7)
            self.play(ShowCreation(arrows[3]), FadeIn(recon), FadeIn(recon_label), FadeIn(objective), FadeIn(formula), FadeIn(reconstruct), run_time=1.0)
            self.wait(1.8)
            self.play(FadeOut(VGroup(title, dense, dense_label, encoder, enc_text, score_text, bars, z_label, decoder, dec_text, dict_text, recon, recon_label, arrows, objective, formula, reconstruct)))

        def topk_definition(self):
            title = self.title(
                "TopK: the rule that makes the code sparse",
                "Keep the K largest feature activations; set every other feature to zero.",
            )

            labels = [f"f{i}" for i in range(1, 11)]
            values = [0.18, 0.93, 0.31, 0.76, 0.12, 0.55, 0.42, 0.88, 0.24, 0.67]
            before = bar_chart(labels, values, width=4.65, height=2.5, hot=set(range(10)))
            before.shift(LEFT * 3.2 + UP * 0.2)
            before_label = txt("raw feature scores", 22, INK, "BOLD").next_to(before, UP, buff=0.25)

            top_indices = {1, 3, 7}
            after = bar_chart(labels, [v if i in top_indices else 0.03 for i, v in enumerate(values)], width=4.65, height=2.5, hot=top_indices)
            after.shift(RIGHT * 3.2 + UP * 0.2)
            after_label = txt("after TopK with K=3", 22, YELLOW_ACCENT, "BOLD").next_to(after, UP, buff=0.25)

            arrow = Arrow(before.get_right(), after.get_left(), buff=0.25).set_stroke(MUTED, 3)
            k_rule = panel(8.6, 1.5, "#171b22").to_edge(DOWN, buff=0.35)
            rule = formula_line(
                [
                    ("TopK_K(z):", YELLOW_ACCENT),
                    (" choose the K biggest entries,", INK),
                    (" zero the rest", RED_ACCENT),
                ],
                size=24,
            )
            rule.move_to(k_rule.get_center() + UP * 0.25)
            project_rule = txt(
                f"In TACO's Octo SAE: K ~= {self.numbers['l0']} active out of {self.numbers['d_sae']} slots, about {100 * self.numbers['l0'] / self.numbers['d_sae']:.1f}% on each step.",
                20,
                MUTED,
            )
            project_rule.set_width(8.1)
            project_rule.move_to(k_rule.get_center() + DOWN * 0.28)

            self.play(FadeIn(title))
            self.play(FadeIn(before), FadeIn(before_label), run_time=0.9)
            self.play(ShowCreation(arrow), FadeIn(after, shift=RIGHT), FadeIn(after_label), run_time=1.1)
            self.play(FadeIn(k_rule), FadeIn(rule), FadeIn(project_rule), run_time=0.8)
            self.wait(1.8)
            self.play(FadeOut(VGroup(title, before, before_label, after, after_label, arrow, k_rule, rule, project_rule)))

        def monitor_definition(self):
            title = self.title(
                "An interpretability monitor is a rule over feature activations",
                "It watches z(t), not just the final behavior.",
            )

            chart_box = panel(7.3, 3.65, "#151b24").shift(LEFT * 1.55 + DOWN * 0.05)
            width = 6.5
            height = 2.5
            axis = Line(LEFT * width / 2, RIGHT * width / 2).set_stroke(MUTED, 2)
            axis.move_to(chart_box.get_center() + DOWN * 1.05)
            yaxis = Line(DOWN * height / 2, UP * height / 2).set_stroke(MUTED, 2)
            yaxis.move_to(chart_box.get_center() + LEFT * width / 2)
            threshold = Line(LEFT * width / 2, RIGHT * width / 2).set_stroke(RED_ACCENT, 2, opacity=0.8)
            threshold.move_to(chart_box.get_center() + UP * 0.38)
            threshold_label = txt("threshold", 17, RED_ACCENT).next_to(threshold, RIGHT, buff=0.08)

            risk_curve = curve_from_points(
                [(0, 0.08), (10, 0.13), (20, 0.18), (30, 0.58), (40, 0.78), (55, 0.88), (80, 0.95)],
                width,
                height,
                YELLOW_ACCENT,
            )
            risk_curve.move_to(chart_box.get_center() + UP * 0.1)
            good_curve = curve_from_points(
                [(0, 0.08), (15, 0.09), (30, 0.13), (45, 0.12), (60, 0.15), (80, 0.13)],
                width,
                height,
                GREEN_ACCENT,
            )
            good_curve.move_to(chart_box.get_center() + UP * 0.1)

            alert_x = -width / 2 + width * int(self.numbers["first_alert_step"]) / int(self.numbers["failure_step"])
            alert_line = Line(
                chart_box.get_center() + np.array([alert_x, -height / 2 + 0.1, 0.0]),
                chart_box.get_center() + np.array([alert_x, height / 2 + 0.1, 0.0]),
            ).set_stroke(YELLOW_ACCENT, 2)
            alert_label = txt("alert", 18, YELLOW_ACCENT, "BOLD").next_to(alert_line, UP, buff=0.08)

            rule_box = panel(3.7, 3.65, "#171b22").shift(RIGHT * 4.15 + DOWN * 0.05)
            rule_title = txt("monitor rule", 25, INK, "BOLD").next_to(rule_box.get_top(), DOWN, buff=0.22)
            rule_lines = VGroup(
                txt("for each timestep t:", 19, MUTED),
                txt("read sparse features z(t)", 19, YELLOW_ACCENT),
                txt("if risk feature > threshold", 19, RED_ACCENT),
                txt("then hand off or slow down", 19, GREEN_ACCENT),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            rule_lines.move_to(rule_box.get_center() + DOWN * 0.1)

            legend = VGroup(
                txt("failure rollout", 18, YELLOW_ACCENT),
                txt("safe rollout", 18, GREEN_ACCENT),
            ).arrange(RIGHT, buff=0.35)
            legend.next_to(chart_box, DOWN, buff=0.18)

            self.play(FadeIn(title), FadeIn(chart_box), FadeIn(axis), FadeIn(yaxis), FadeIn(rule_box), FadeIn(rule_title))
            self.play(ShowCreation(good_curve), ShowCreation(risk_curve), ShowCreation(threshold), FadeIn(threshold_label), FadeIn(legend), run_time=1.2)
            self.play(ShowCreation(alert_line), FadeIn(alert_label), FadeIn(rule_lines, shift=UP), run_time=1.0)
            self.wait(1.7)
            self.play(FadeOut(VGroup(title, chart_box, axis, yaxis, threshold, threshold_label, risk_curve, good_curve, alert_line, alert_label, rule_box, rule_title, rule_lines, legend)))

        def black_box_to_activations(self):
            title = self.title("A replay shows behavior. Internals show timing.")

            camera = panel(3.0, 2.2, "#182026")
            camera.shift(LEFT * 4.3 + DOWN * 0.2)
            frame_title = txt("camera + instruction", 20, MUTED)
            frame_title.next_to(camera, UP, buff=0.12)
            table = Rectangle(width=2.4, height=0.28).set_fill("#404850", 1).set_stroke("#404850", 0)
            table.move_to(camera.get_center() + DOWN * 0.55)
            arm = VGroup(
                Line(camera.get_center() + LEFT * 0.7 + UP * 0.65, camera.get_center() + LEFT * 0.15 + UP * 0.05),
                Line(camera.get_center() + LEFT * 0.15 + UP * 0.05, camera.get_center() + RIGHT * 0.25 + DOWN * 0.25),
                Circle(radius=0.1).move_to(camera.get_center() + RIGHT * 0.3 + DOWN * 0.3),
            )
            arm.set_stroke(BLUE_ACCENT, width=5)
            obj = Circle(radius=0.17).set_fill(YELLOW_ACCENT, 1).set_stroke(YELLOW_ACCENT, 0)
            obj.move_to(camera.get_center() + RIGHT * 0.75 + DOWN * 0.43)
            instruction = txt('"move near orange"', 19, INK)
            instruction.move_to(camera.get_center() + UP * 0.75)
            camera_group = VGroup(camera, frame_title, table, arm, obj, instruction)

            policy = panel(2.45, 1.55, "#11151b")
            policy.move_to(LEFT * 0.65 + DOWN * 0.2)
            policy_label = txt("VLA policy", 28, INK, "BOLD").move_to(policy)
            dense = vector_lights(4, 8, {2, 5, 9, 13, 17, 21, 30}, cell=0.18)
            dense.scale(0.8)
            dense.next_to(policy, DOWN, buff=0.25)
            policy_group = VGroup(policy, policy_label, dense, small_label("dense residual stream", dense))

            outcome = panel(3.05, 2.2, "#22191a")
            outcome.shift(RIGHT * 3.75 + DOWN * 0.2)
            ok_path = VMobject()
            ok_path.set_points_as_corners([
                outcome.get_center() + LEFT * 0.9 + DOWN * 0.35,
                outcome.get_center() + LEFT * 0.35 + DOWN * 0.1,
                outcome.get_center() + RIGHT * 0.2 + UP * 0.05,
                outcome.get_center() + RIGHT * 0.85 + UP * 0.35,
            ])
            ok_path.set_stroke(GREEN_ACCENT, width=5)
            fail_path = VMobject()
            fail_path.set_points_as_corners([
                outcome.get_center() + LEFT * 0.9 + DOWN * 0.35,
                outcome.get_center() + LEFT * 0.2 + DOWN * 0.15,
                outcome.get_center() + RIGHT * 0.2 + DOWN * 0.35,
                outcome.get_center() + RIGHT * 0.85 + DOWN * 0.65,
            ])
            fail_path.set_stroke(RED_ACCENT, width=5)
            out_label = txt("visible trajectory", 20, MUTED)
            out_label.next_to(outcome, UP, buff=0.12)
            failure = txt("failure", 28, RED_ACCENT, "BOLD")
            failure.move_to(outcome.get_center() + DOWN * 0.78)
            outcome_group = VGroup(outcome, out_label, ok_path, failure)

            in_arrow = Arrow(camera.get_right(), policy.get_left(), buff=0.2)
            out_arrow = Arrow(policy.get_right(), outcome.get_left(), buff=0.2)
            for arrow in (in_arrow, out_arrow):
                arrow.set_stroke(MUTED, width=3)

            self.play(FadeIn(title))
            self.play(FadeIn(camera_group, shift=RIGHT), ShowCreation(in_arrow), FadeIn(policy_group), run_time=1.2)
            self.play(ShowCreation(out_arrow), FadeIn(outcome), FadeIn(out_label), ShowCreation(ok_path), run_time=1.0)
            self.play(Transform(ok_path, fail_path), FadeIn(failure, shift=UP), dense.animate.scale(1.12), run_time=1.3)
            note = txt("The replay says what happened. The activations say when the risk started.", 24, INK)
            note.to_edge(DOWN, buff=0.45)
            self.play(FadeIn(note, shift=UP))
            self.wait(1.3)
            self.play(FadeOut(VGroup(title, camera_group, policy_group, outcome_group, in_arrow, out_arrow, note)))

        def sae_prism(self):
            title = self.title("A sparse autoencoder acts like a prism")
            dense = vector_lights(8, 8, {3, 5, 7, 11, 13, 21, 22, 34, 39, 42, 50, 56, 61}, cell=0.15)
            dense.shift(LEFT * 4.35)
            dense_label = txt(f"{self.numbers['d_model']} mixed dimensions", 22, MUTED)
            dense_label.next_to(dense, DOWN, buff=0.25)

            encoder = Polygon(LEFT * 0.8 + DOWN * 1.15, LEFT * 0.8 + UP * 1.15, RIGHT * 0.75)
            encoder.set_fill("#243044", 1).set_stroke(BLUE_ACCENT, width=2)
            encoder.move_to(LEFT * 1.15)
            enc_label = txt("TopK SAE", 28, INK, "BOLD").move_to(encoder)
            enc_sub = txt("learned dictionary", 18, MUTED)
            enc_sub.next_to(enc_label, DOWN, buff=0.08)

            bars = sparse_bars(36, hot=(4, 12, 22, 31))
            bars.scale(0.95)
            bars.shift(RIGHT * 1.75 + DOWN * 0.35)
            sparse_label = txt(f"{self.numbers['d_sae']} feature slots; only {self.numbers['l0']} active", 22, MUTED)
            sparse_label.next_to(bars, DOWN, buff=0.25)

            labels = VGroup(
                txt("grasp primitive", 16, GREEN_ACCENT),
                txt("task progress", 16, BLUE_ACCENT),
                txt("language target", 16, YELLOW_ACCENT),
                txt("memorized replay", 16, PURPLE_ACCENT),
            )
            labels.arrange(DOWN, aligned_edge=LEFT, buff=0.13)
            labels.next_to(bars, RIGHT, buff=0.22)

            arrow1 = Arrow(dense.get_right(), encoder.get_left(), buff=0.15).set_stroke(MUTED, 3)
            arrow2 = Arrow(encoder.get_right(), bars.get_left(), buff=0.15).set_stroke(MUTED, 3)

            ev = metric_card("Reconstruction EV", f"{100 * self.numbers['explained_variance']:.1f}%", width=2.6, accent=GREEN_ACCENT)
            ev.to_edge(DOWN, buff=0.35).shift(LEFT * 1.4)
            alive = metric_card("Alive features", f"{self.numbers['alive_features']:,}", width=2.25, accent=BLUE_ACCENT)
            alive.next_to(ev, RIGHT, buff=0.25)
            samples = metric_card("Rollout samples", f"{self.numbers['n_samples']:,}", width=2.35, accent=YELLOW_ACCENT)
            samples.next_to(alive, RIGHT, buff=0.25)

            self.play(FadeIn(title))
            self.play(FadeIn(dense), FadeIn(dense_label), run_time=0.8)
            self.play(ShowCreation(arrow1), FadeIn(encoder), FadeIn(enc_label), FadeIn(enc_sub), run_time=0.9)
            self.play(ShowCreation(arrow2), FadeIn(bars, shift=RIGHT), FadeIn(sparse_label), run_time=1.1)
            self.play(*[FadeIn(label, shift=RIGHT) for label in labels], FadeIn(ev), FadeIn(alive), FadeIn(samples))
            self.wait(1.5)
            self.play(FadeOut(VGroup(title, dense, dense_label, encoder, enc_label, enc_sub, bars, sparse_label, labels, arrow1, arrow2, ev, alive, samples)))

        def general_vs_memorized(self):
            title = self.title("Not every feature is certification-grade")
            left_box = panel(4.3, 3.2, "#17211a").shift(LEFT * 2.65 + DOWN * 0.15)
            right_box = panel(4.3, 3.2, "#221a24").shift(RIGHT * 2.65 + DOWN * 0.15)
            left_title = txt("general feature", 28, GREEN_ACCENT, "BOLD").next_to(left_box, UP, buff=0.18)
            right_title = txt("memorized feature", 28, PURPLE_ACCENT, "BOLD").next_to(right_box, UP, buff=0.18)

            gen_curves = VGroup()
            for offset, opacity in [(-0.18, 0.5), (0.0, 1.0), (0.18, 0.5)]:
                points = [(0, 0.08), (12, 0.25 + offset), (24, 0.8 + offset), (36, 0.95), (48, 0.55 + offset), (60, 0.22)]
                c = curve_from_points(points, 3.4, 1.7, GREEN_ACCENT)
                c.set_opacity(opacity)
                c.move_to(left_box.get_center() + DOWN * 0.1)
                gen_curves.add(c)

            mem_curve = curve_from_points(
                [(0, 0.05), (15, 0.08), (24, 0.95), (30, 0.18), (45, 0.06), (60, 0.05)],
                3.4,
                1.7,
                PURPLE_ACCENT,
            )
            mem_curve.move_to(right_box.get_center() + DOWN * 0.1)
            faint_mem = mem_curve.copy().set_opacity(0.25).shift(UP * 0.25)

            gen_notes = VGroup(
                txt("fires across scenes", 15, INK),
                txt("phase-aligned with behavior", 15, INK),
                txt("candidate for a monitor", 15, INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            gen_notes.move_to(left_box.get_center() + DOWN * 0.82)
            mem_notes = VGroup(
                txt("tied to one replay", 15, INK),
                txt("can vanish under perturbation", 15, INK),
                txt("not enough by itself", 15, INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            mem_notes.move_to(right_box.get_center() + DOWN * 0.82)

            self.play(FadeIn(title), FadeIn(left_box), FadeIn(right_box), FadeIn(left_title), FadeIn(right_title))
            self.play(*[ShowCreation(c) for c in gen_curves], run_time=1.1)
            self.play(ShowCreation(mem_curve), FadeIn(faint_mem), run_time=0.9)
            self.play(FadeIn(gen_notes, shift=UP), FadeIn(mem_notes, shift=UP))
            self.wait(1.4)
            self.play(FadeOut(VGroup(title, left_box, right_box, left_title, right_title, gen_curves, mem_curve, faint_mem, gen_notes, mem_notes)))

        def dreamaudit_timeline(self):
            title = self.title("DreamAudit turns a hint into replayable evidence")
            width = 8.8
            height = 2.6
            box = panel(width + 0.55, height + 1.25, "#151b24").shift(DOWN * 0.1)
            axis = Line(LEFT * width / 2, RIGHT * width / 2).set_stroke(MUTED, 2)
            axis.move_to(box.get_center() + DOWN * 1.02)
            zero = txt("0", 16, MUTED).next_to(axis.get_left(), DOWN, buff=0.08)
            end = txt(str(self.numbers["failure_step"]), 16, MUTED).next_to(axis.get_right(), DOWN, buff=0.08)
            threshold = Line(LEFT * width / 2, RIGHT * width / 2).set_stroke("#5d6675", 1.5)
            threshold.move_to(box.get_center() + UP * 0.45)
            threshold_label = txt("monitor threshold", 16, MUTED).next_to(threshold, RIGHT, buff=0.08)

            max_step = int(self.numbers["failure_step"])
            internal = curve_from_points(
                [(0, 0.1), (12, 0.15), (24, 0.35), (32, 0.78), (48, 0.92), (64, 0.98), (max_step, 1.0)],
                width,
                height,
                YELLOW_ACCENT,
            )
            action = curve_from_points(
                [(0, 0.05), (24, 0.08), (40, 0.16), (56, 0.75), (max_step, 0.95)],
                width,
                height,
                BLUE_ACCENT,
            )
            internal.move_to(box.get_center() + UP * 0.05)
            action.move_to(box.get_center() + UP * 0.05)

            m1 = timeline_marker(int(self.numbers["first_alert_step"]), max_step, width, height, YELLOW_ACCENT, "SAE alert t=32")
            m1.move_to(box.get_center() + UP * 0.05)
            m2 = timeline_marker(int(self.numbers["action_alert_step"]), max_step, width, height, BLUE_ACCENT, "action alert t=56")
            m2.move_to(box.get_center() + UP * 0.05)
            m3 = timeline_marker(max_step, max_step, width, height, RED_ACCENT, "failure")
            m3.move_to(box.get_center() + UP * 0.05)

            bracket_y = box.get_center()[1] + height / 2 + 0.35
            bracket_left = np.array([m1[0].get_top()[0], bracket_y, 0.0])
            bracket_right = np.array([m3[0].get_top()[0], bracket_y, 0.0])
            brace = VGroup(
                Line(bracket_left, bracket_right),
                Line(bracket_left, bracket_left + DOWN * 0.18),
                Line(bracket_right, bracket_right + DOWN * 0.18),
            )
            brace.set_stroke(YELLOW_ACCENT, 2)
            lead = txt(f"{self.numbers['lead_steps']}-step warning lead", 24, YELLOW_ACCENT, "BOLD")
            lead.next_to(brace, UP, buff=0.1)

            legend = VGroup(
                txt("internal SAE monitor", 18, YELLOW_ACCENT),
                txt("action diagnostic", 18, BLUE_ACCENT),
                txt(f"recall {self.numbers['recall']:.1f}; precision {self.numbers['precision']:.3f}", 18, INK),
            ).arrange(RIGHT, buff=0.35)
            legend.next_to(box, DOWN, buff=0.22)

            perturb = txt("minimal perturbation replay", 22, RED_ACCENT, "BOLD")
            perturb.next_to(box, UP, buff=0.25)

            self.play(FadeIn(title), FadeIn(box), FadeIn(axis), FadeIn(zero), FadeIn(end), FadeIn(perturb))
            self.play(ShowCreation(threshold), FadeIn(threshold_label))
            self.play(ShowCreation(internal), ShowCreation(action), run_time=1.4)
            self.play(FadeIn(m1), FadeIn(m2), FadeIn(m3), ShowCreation(brace), FadeIn(lead), FadeIn(legend), run_time=1.1)
            self.wait(1.7)
            self.play(FadeOut(VGroup(title, box, axis, zero, end, threshold, threshold_label, internal, action, m1, m2, m3, brace, lead, legend, perturb)))

        def certification_translation(self):
            title = self.title("TACO certifies readiness, not vibes")
            evidence = VGroup(
                metric_card("Replay", "real rollout", width=2.15, accent=BLUE_ACCENT),
                metric_card("Certificate", str(self.numbers.get("certificate", "FR-004")), width=2.15, accent=YELLOW_ACCENT),
                metric_card("Internal signal", f"t={self.numbers['first_alert_step']}", width=2.15, accent=GREEN_ACCENT),
                metric_card("Limitation", f"{self.numbers['false_alert_count']} false handoff", width=2.25, accent=PURPLE_ACCENT),
            )
            evidence.arrange(RIGHT, buff=0.22)
            evidence.shift(UP * 1.45)

            certificate = panel(7.7, 2.65, "#181d27").shift(DOWN * 1.0)
            certificate_title = txt("Pre-deployment readiness certificate", 28, INK, "BOLD")
            certificate_title.next_to(certificate.get_top(), DOWN, buff=0.22)
            rows = VGroup(
                txt("Tier: Monitorable with required control", 21, GREEN_ACCENT),
                txt("Failure mode: identified from model internals", 19, INK),
                txt("Condition: re-audit if monitor is disabled or unverified", 19, RED_ACCENT),
            )
            rows.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            rows.move_to(certificate.get_center() + DOWN * 0.22)
            certificate_group = VGroup(certificate, certificate_title, rows)

            arrows = VGroup()
            for card in evidence:
                arr = Arrow(card.get_bottom(), certificate.get_top(), buff=0.1)
                arr.set_stroke(MUTED, width=2)
                arrows.add(arr)

            self.play(FadeIn(title))
            self.play(*[FadeIn(card, shift=DOWN) for card in evidence], run_time=1.0)
            self.play(*[ShowCreation(arr) for arr in arrows], FadeIn(certificate_group, shift=UP), run_time=1.2)
            self.wait(1.6)
            self.play(FadeOut(VGroup(title, evidence, arrows, certificate_group)))

        def final_frame(self):
            title = self.title("The certification claim")
            chain = VGroup(
                txt("SAE features", 28, BLUE_ACCENT, "BOLD"),
                txt("+", 34, MUTED, "BOLD"),
                txt("DreamAudit replay", 28, YELLOW_ACCENT, "BOLD"),
                txt("+", 34, MUTED, "BOLD"),
                txt("runtime monitor", 28, GREEN_ACCENT, "BOLD"),
                txt("=>", 34, MUTED, "BOLD"),
                txt("readiness tier", 28, INK, "BOLD"),
            )
            chain.arrange(RIGHT, buff=0.22)
            chain.move_to(UP * 0.45)
            caution = VGroup(
                txt("The demo does not claim every feature is causal.", 22, MUTED),
                txt(
                    "It claims internals can identify failure modes early enough to issue a conditional certificate.",
                    22,
                    MUTED,
                ),
            ).arrange(DOWN, buff=0.12)
            if caution.get_width() > 10.6:
                caution.set_width(10.6)
            caution.next_to(chain, DOWN, buff=0.55)
            self.play(FadeIn(title), FadeIn(chain, shift=UP), FadeIn(caution, shift=UP))
            self.wait(2.0)


    class Explainer01Opening(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.opening()


    class Explainer02Activations(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.activation_vocabulary()


    class Explainer03Features(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.what_is_a_feature()


    class Explainer04Superposition(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.superposition_problem()


    class Explainer05SAEMechanics(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.sae_mechanics()


    class Explainer06TopK(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.topk_definition()


    class Explainer07MonitorRule(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.monitor_definition()


    class Explainer08ReplayTiming(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.black_box_to_activations()


    class Explainer09SAEPrism(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.sae_prism()


    class Explainer10FeatureQuality(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.general_vs_memorized()


    class Explainer11DreamAudit(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.dreamaudit_timeline()


    class Explainer12Insurance(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.certification_translation()


    class Explainer12Certification(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.certification_translation()


    class Explainer13Claim(TacoSAEDreamAuditExplainer):
        def construct(self):
            self.final_frame()
