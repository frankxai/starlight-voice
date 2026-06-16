/* ============================================================================
   Starlight Voice — landing motion. Zero dependencies.
   Principles: progressive enhancement (content lives without JS), and a hard
   reduced-motion bail so the canvas + scroll choreography never fight a user
   who asked for stillness.
   ========================================================================== */
(() => {
  "use strict";
  const doc = document.documentElement;
  doc.classList.remove("no-js");
  doc.classList.add("js");

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── scroll progress rail + condensing nav ─────────────────────────────── */
  const fill = document.getElementById("scrollFill");
  const nav = document.getElementById("nav");
  let ticking = false;
  const onScroll = () => {
    const h = doc.scrollHeight - doc.clientHeight;
    const p = h > 0 ? (window.scrollY / h) * 100 : 0;
    if (fill) fill.style.width = p + "%";
    if (nav) nav.classList.toggle("scrolled", window.scrollY > 24);
    ticking = false;
  };
  window.addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        window.requestAnimationFrame(onScroll);
        ticking = true;
      }
    },
    { passive: true }
  );
  onScroll();

  /* ── reveal-on-scroll (+ pipeline pulse + count-up trigger) ────────────── */
  const reveals = Array.from(document.querySelectorAll(".reveal"));
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach((el) => el.classList.add("in"));
    document.getElementById("pipeline")?.classList.add("lit");
    runCounts();
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          e.target.classList.add("in");
          if (e.target.id === "pipeline") e.target.classList.add("lit");
          if (e.target.querySelector?.(".count") || e.target.classList.contains("count")) {
            runCounts(e.target);
          }
          io.unobserve(e.target);
        });
      },
      { threshold: 0.18, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach((el) => io.observe(el));
    // pipeline may not carry .reveal on its own — observe explicitly
    const pipe = document.getElementById("pipeline");
    if (pipe && !pipe.classList.contains("reveal")) io.observe(pipe);
  }

  /* ── count-up numbers (honours the data-to / data-suffix on .count) ────── */
  function runCounts(scope) {
    const root = scope && scope.querySelectorAll ? scope : document;
    root.querySelectorAll(".count:not([data-done])").forEach((node) => {
      const to = parseFloat(node.dataset.to || "0");
      const suffix = node.dataset.suffix || "";
      node.dataset.done = "1";
      if (reduce) {
        node.textContent = to + suffix;
        return;
      }
      const dur = 1100;
      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
        node.textContent = Math.round(to * eased) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  /* ── pointer tilt on cards (subtle, GPU-cheap, pointer-only) ───────────── */
  if (!reduce && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll("[data-tilt]").forEach((card) => {
      card.addEventListener("pointermove", (ev) => {
        const r = card.getBoundingClientRect();
        const x = (ev.clientX - r.left) / r.width - 0.5;
        const y = (ev.clientY - r.top) / r.height - 0.5;
        card.style.transform = `perspective(800px) rotateX(${(-y * 5).toFixed(2)}deg) rotateY(${(
          x * 5
        ).toFixed(2)}deg) translateY(-4px)`;
      });
      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  }

  /* ── hero canvas: a slow constellation with a voltage waveform spine ───── */
  const canvas = document.getElementById("heroCanvas");
  if (canvas && !reduce) {
    const ctx = canvas.getContext("2d");
    let w = 0;
    let h = 0;
    let dpr = 1;
    let raf = 0;
    const NODES = 56;
    const pts = [];

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const seed = () => {
      pts.length = 0;
      for (let i = 0; i < NODES; i++) {
        pts.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.22,
          vy: (Math.random() - 0.5) * 0.22,
          r: Math.random() * 1.6 + 0.6,
        });
      }
    };

    const draw = (time) => {
      ctx.clearRect(0, 0, w, h);

      // links between near nodes
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i];
        a.x += a.vx;
        a.y += a.vy;
        if (a.x < 0 || a.x > w) a.vx *= -1;
        if (a.y < 0 || a.y > h) a.vy *= -1;
        for (let j = i + 1; j < pts.length; j++) {
          const b = pts[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 19000) {
            const alpha = (1 - d2 / 19000) * 0.32;
            ctx.strokeStyle = `rgba(110,92,255,${alpha.toFixed(3)})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      // node glow-points
      for (const p of pts) {
        ctx.fillStyle = "rgba(185,166,255,0.6)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }

      // the waveform spine — a living voice signature across the midline
      const midY = h * 0.5;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 6) {
        const k = x / w;
        const env = Math.sin(k * Math.PI); // taper at the edges
        const y =
          midY +
          Math.sin(k * 26 + time * 0.0016) * 16 * env +
          Math.sin(k * 11 - time * 0.0011) * 26 * env;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      const grad = ctx.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, "rgba(110,92,255,0)");
      grad.addColorStop(0.5, "rgba(110,92,255,0.5)");
      grad.addColorStop(1, "rgba(224,182,86,0)");
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      raf = requestAnimationFrame(draw);
    };

    const start = () => {
      resize();
      seed();
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(draw);
    };

    // pause when scrolled past the hero (don't burn cycles offscreen)
    const visObs = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          raf = requestAnimationFrame(draw);
        } else {
          cancelAnimationFrame(raf);
        }
      },
      { threshold: 0 }
    );
    visObs.observe(canvas);

    window.addEventListener("resize", () => {
      resize();
      seed();
    });
    start();
  }
})();
