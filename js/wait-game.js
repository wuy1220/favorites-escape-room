/* 纸页夜奔(2026-08-30 v3):生成等待期小游戏。
   你是深夜工房里一页成精的纸片,趁起草人不注意沿书桌奔跑;
   跳过墨水瓶/胶带卷/纸团,收集散落的纸页——每张纸页在页边解锁一句工房手记
   (window.__wbNoteReveal 由 app.js 注入,与定时手记共享同一个文案池)。
   物理与失败契约(2026-08-30 v3 修订):
   - 固定步长 60Hz 逻辑步 + rAF 累加器——速度/跳跃/密度与屏幕刷新率解耦
     (按帧驱动在 120/144Hz 屏上整体加速 2-2.4 倍);
   - 速度曲线 2.4→4.6 px/步,障碍间距按「距离」生成,不随帧率压缩;
   - 失败判定必须可见:3 滴墨(命),撞上障碍扣一滴——命中停顿+画面震动+
     1.1s 无敌闪烁;墨尽 = 本局结束(成绩结算 + 点击再来一局);
   - 判定盒宽松:跑者盒四周收紧,擦边不扣墨;无敌帧防一障多扣;
   - __wbGame.__debug 暴露单步驱动与状态快照,供回归测试模拟整局。 */
(function () {
  'use strict';
  const PAL = {
    paper: '#f7f1e3',
    ink: '#2c2a26',
    inkSoft: 'rgba(44,42,38,0.35)',
    seal: '#b23a2c',
    ground: 'rgba(44,42,38,0.45)',
  };
  const STEP_MS = 1000 / 60; /* 逻辑步长:与刷新率解耦 */
  const GRAV = 0.4,
    JUMP = -7.8;
  const SPEED0 = 2.4,
    SPEED_MAX = 4.6;
  let cv = null,
    ctx = null,
    raf = 0,
    started = false,
    running = false,
    last = 0,
    acc = 0;
  const S = {
    w: 0,
    h: 0,
    groundY: 0,
    t: 0,
    speed: SPEED0,
    dist: 0,
    pages: 0,
    lives: 3,
    inv: 0,
    shake: 0,
    gameOver: false,
    runner: { x: 70, y: 0, w: 20, h: 26, vy: 0, onGround: true, dead: 0 },
    obs: [],
    cols: [],
    nextObsD: 260,
    nextColD: 180,
    floaters: [],
  };
  function fit() {
    if (!cv) return;
    const r = cv.getBoundingClientRect();
    S.w = Math.max(320, Math.round(r.width) || 640);
    S.h = 150;
    cv.width = S.w;
    cv.height = S.h;
    S.groundY = S.h - 26;
  }
  function reset() {
    fit();
    S.t = 0;
    S.speed = SPEED0;
    S.dist = 0;
    S.pages = 0;
    S.lives = 3;
    S.inv = 0;
    S.shake = 0;
    S.gameOver = false;
    S.obs = [];
    S.cols = [];
    S.floaters = [];
    S.nextObsD = 260;
    S.nextColD = 180;
    S.runner.y = S.groundY - S.runner.h;
    S.runner.vy = 0;
    S.runner.onGround = true;
    S.runner.dead = 0;
  }
  function jump() {
    if (!running || S.gameOver || S.runner.dead > 0) return;
    if (S.runner.onGround) {
      S.runner.vy = JUMP;
      S.runner.onGround = false;
    }
  }
  function spawnObstacle() {
    const kinds = ['ink', 'tape', 'ball'];
    const k = kinds[Math.floor(Math.random() * kinds.length)];
    S.obs.push({ k, x: S.w + 20, y: S.groundY });
  }
  function spawnCollectible() {
    const high = Math.random() < 0.45;
    S.cols.push({
      x: S.w + 20,
      y: high ? S.groundY - 54 : S.groundY - 14,
      got: 0,
    });
  }
  /* 跑者判定盒:四周收紧(顶 2px/前后 4px/底 3px)——擦边不扣墨 */
  function runnerBox() {
    const R = S.runner;
    return { x: R.x + 4, y: R.y + 2, w: R.w - 8, h: R.h - 3 };
  }
  function hit() {
    S.lives--;
    S.inv = 66; /* 1.1s 无敌:同一障碍/贴身连续障碍不重复扣墨 */
    S.shake = 14;
    S.floaters.push({ x: S.runner.x + 12, y: S.runner.y - 8, txt: '哗啦——', t: 44 });
    if (S.lives <= 0) {
      S.lives = 0;
      S.gameOver = true;
    }
  }
  function logicStep() {
    S.t++;
    if (S.shake > 0) S.shake--;
    if (S.inv > 0) S.inv--;
    S.floaters.forEach((f) => {
      f.t--;
      f.y -= 0.5;
    });
    S.floaters = S.floaters.filter((f) => f.t > 0);
    if (S.gameOver) return; /* 结算画面冻结世界,等点击重开 */
    S.dist += S.speed;
    S.speed = Math.min(SPEED_MAX, SPEED0 + S.dist / 1400);
    const R = S.runner;
    if (R.dead > 0) {
      R.dead--;
    } else {
      if (!R.onGround) {
        R.vy += GRAV;
        R.y += R.vy;
        if (R.y >= S.groundY - R.h) {
          R.y = S.groundY - R.h;
          R.vy = 0;
          R.onGround = true;
        }
      }
      /* 生成按「距离」计:间距不随刷新率/速度压缩 */
      S.nextObsD -= S.speed;
      if (S.nextObsD <= 0) {
        spawnObstacle();
        S.nextObsD = 240 + Math.random() * 220;
      }
      S.nextColD -= S.speed;
      if (S.nextColD <= 0) {
        spawnCollectible();
        S.nextColD = 200 + Math.random() * 300;
      }
      const rb = runnerBox();
      for (const o of S.obs) {
        o.x -= S.speed;
        if (S.inv > 0) continue; /* 无敌帧:穿透不判 */
        const box =
          o.k === 'tape'
            ? { x: o.x - 8, y: o.y - 17, w: 16, h: 17 }
            : o.k === 'ball'
              ? { x: o.x - 7, y: o.y - 14, w: 14, h: 14 }
              : { x: o.x - 6, y: o.y - 21, w: 12, h: 21 };
        if (
          rb.x < box.x + box.w &&
          rb.x + rb.w > box.x &&
          rb.y < box.y + box.h &&
          rb.y + rb.h > box.y
        ) {
          R.dead = 12; /* 命中停顿 0.2s */
          hit();
        }
      }
      S.obs = S.obs.filter((o) => o.x > -30);
      for (const c of S.cols) {
        c.x -= S.speed;
        if (
          !c.got &&
          rb.x < c.x + 8 &&
          rb.x + rb.w > c.x - 8 &&
          rb.y < c.y + 12 &&
          rb.y + rb.h > c.y - 12
        ) {
          c.got = 1;
          S.pages++;
          S.floaters.push({ x: c.x, y: c.y - 8, txt: '+1', t: 36 });
          if (typeof window.__wbNoteReveal === 'function') window.__wbNoteReveal();
        }
      }
      S.cols = S.cols.filter((c) => c.x > -20 && !c.got);
    }
  }
  function draw() {
    ctx.save();
    if (S.shake > 0) {
      ctx.translate((Math.random() - 0.5) * 5, (Math.random() - 0.5) * 4);
    }
    ctx.clearRect(-6, -6, S.w + 12, S.h + 12);
    ctx.strokeStyle = PAL.ground;
    ctx.beginPath();
    ctx.moveTo(0, S.groundY + 0.5);
    ctx.lineTo(S.w, S.groundY + 0.5);
    ctx.stroke();
    ctx.fillStyle = PAL.inkSoft;
    for (let x = -(Math.floor(S.dist) % 46); x < S.w; x += 46) {
      ctx.fillRect(x, S.groundY + 8, 22, 2);
    }
    const R = S.runner;
    const blink = S.inv > 0 && Math.floor(S.inv / 5) % 2 === 0;
    if (!blink) {
      const flutter = R.onGround ? Math.sin(S.t / 6) * 1.2 : -2;
      ctx.save();
      ctx.translate(R.x + R.w / 2, R.y + R.h / 2);
      ctx.rotate(((R.onGround ? flutter : -6) * Math.PI) / 180);
      ctx.fillStyle = PAL.paper;
      ctx.strokeStyle = PAL.ink;
      ctx.lineWidth = 1.2;
      ctx.fillRect(-R.w / 2, -R.h / 2, R.w, R.h);
      ctx.strokeRect(-R.w / 2, -R.h / 2, R.w, R.h);
      ctx.fillStyle = PAL.seal;
      ctx.fillRect(-R.w / 2 + 4, -R.h / 2 + 4, 5, 5);
      ctx.restore();
    }
    for (const o of S.obs) {
      ctx.fillStyle = PAL.ink;
      if (o.k === 'ink') {
        ctx.fillRect(o.x - 5, o.y - 8, 10, 8);
        ctx.fillRect(o.x - 2.5, o.y - 21, 5, 13);
        ctx.fillStyle = PAL.inkSoft;
        ctx.fillRect(o.x - 2.5, o.y - 14, 5, 6);
      } else if (o.k === 'tape') {
        ctx.strokeStyle = PAL.ink;
        ctx.beginPath();
        ctx.arc(o.x, o.y - 9, 9, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(o.x, o.y - 9, 3.2, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        ctx.strokeStyle = PAL.ink;
        ctx.beginPath();
        ctx.moveTo(o.x - 8, o.y - 2);
        ctx.lineTo(o.x - 3, o.y - 14);
        ctx.lineTo(o.x + 5, o.y - 12);
        ctx.lineTo(o.x + 8, o.y - 3);
        ctx.closePath();
        ctx.stroke();
      }
    }
    for (const c of S.cols) {
      ctx.save();
      ctx.translate(c.x, c.y + Math.sin((S.t + c.x) / 14) * 2);
      ctx.rotate(0.25);
      ctx.fillStyle = PAL.paper;
      ctx.strokeStyle = PAL.ink;
      ctx.fillRect(-5, -7, 10, 14);
      ctx.strokeRect(-5, -7, 10, 14);
      ctx.strokeStyle = PAL.inkSoft;
      ctx.beginPath();
      ctx.moveTo(-3, -3);
      ctx.lineTo(3, -3);
      ctx.moveTo(-3, 1);
      ctx.lineTo(3, 1);
      ctx.stroke();
      ctx.restore();
    }
    ctx.fillStyle = PAL.ink;
    ctx.font = '12px sans-serif';
    for (const f of S.floaters) {
      ctx.globalAlpha = Math.min(1, f.t / 18);
      ctx.fillText(f.txt, f.x, f.y);
    }
    ctx.globalAlpha = 1;
    /* 墨量(命)与里程 */
    ctx.textAlign = 'left';
    for (let i = 0; i < 3; i++) {
      ctx.globalAlpha = i < S.lives ? 0.85 : 0.15;
      ctx.beginPath();
      ctx.arc(14 + i * 16, 16, 5, 0, Math.PI * 2);
      ctx.fillStyle = PAL.ink;
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = PAL.inkSoft;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(
      '今晚翻过了 ' + Math.floor(S.dist / 10) + ' 页 · 收集手记 ' + S.pages + ' 句',
      S.w - 10,
      16,
    );
    if (S.gameOver) {
      ctx.fillStyle = 'rgba(250,246,235,0.82)';
      ctx.fillRect(0, 0, S.w, S.h);
      ctx.fillStyle = PAL.ink;
      ctx.font = '15px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('纸页合上了。', S.w / 2, S.h / 2 - 16);
      ctx.font = '12px sans-serif';
      ctx.fillText(
        '今晚翻过了 ' + Math.floor(S.dist / 10) + ' 页 · 收集手记 ' + S.pages + ' 句',
        S.w / 2,
        S.h / 2 + 6,
      );
      ctx.fillStyle = PAL.seal;
      ctx.fillText('点击桌面,再来一局', S.w / 2, S.h / 2 + 30);
      ctx.textAlign = 'left';
    }
    ctx.textAlign = 'left';
    ctx.restore();
  }
  function frame(now) {
    if (!running) return;
    if (!last) last = now;
    acc += Math.min(100, now - last); /* 后台/卡顿封顶,防大步穿越 */
    last = now;
    while (acc >= STEP_MS) {
      logicStep();
      acc -= STEP_MS;
    }
    draw();
    raf = requestAnimationFrame(frame);
  }
  function start() {
    if (!bind()) return;
    if (!started) {
      started = true;
      reset();
    } else {
      fit();
    }
    if (running) return;
    running = true;
    last = 0;
    acc = 0;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(frame);
  }
  function pause() {
    running = false;
    cancelAnimationFrame(raf);
  }
  function stop() {
    pause();
    started = false;
  }
  function restart() {
    reset();
    if (!running) {
      running = true;
      last = 0;
      acc = 0;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(frame);
    }
  }
  let bound = false;
  function bind() {
    cv = document.getElementById('wbGameCanvas');
    if (!cv) return false; /* canvas 由 addUi 动态注入——惰性绑定,start 时重试 */
    if (!bound) {
      bound = true;
      ctx = cv.getContext('2d');
      cv.addEventListener('click', function () {
        if (S.gameOver) restart();
        else jump();
      });
      cv.addEventListener('touchstart', function (e) {
        e.preventDefault();
        if (S.gameOver) restart();
        else jump();
      });
      window.addEventListener('keydown', function (e) {
        if (!started || !running) return;
        if (e.code === 'Space' || e.code === 'ArrowUp') {
          e.preventDefault();
          if (S.gameOver) restart();
          else jump();
        }
      });
      document.addEventListener('visibilitychange', function () {
        if (document.hidden) pause();
      });
    }
    return true;
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
  window.__wbGame = {
    start,
    pause,
    stop,
    jump,
    isStarted: () => started,
    /* 回归测试钩子:单步驱动 + 状态快照,不经过 rAF */
    __debug: {
      S,
      logicStep,
      run(n) {
        for (let i = 0; i < n; i++) logicStep();
      },
      spawnObstacle,
      spawnCollectible,
      restart,
      state() {
        return {
          lives: S.lives,
          deaths: 3 - S.lives,
          pages: S.pages,
          gameOver: S.gameOver,
          inv: S.inv,
          speed: Math.round(S.speed * 100) / 100,
          runnerY: Math.round(S.runner.y),
          obsX: S.obs.map((o) => Math.round(o.x)),
        };
      },
    },
  };
})();
