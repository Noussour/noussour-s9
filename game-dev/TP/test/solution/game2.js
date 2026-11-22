// ============================================================================
// Angry Birds - VERSION 2 (key 2)
//   3 birds, score and best score, destroyable blocks (wood, ice, rock),
//   win when the pig touches the ground with 1 to 3 stars (fewer birds used =
//   more stars, 0 stars when the pig survives), sound effects, modern interface
//   with clickable buttons, and a tutorial shown at the start.
//
// AI USED: this whole file was written with Claude Code (AI assistant).
// Prompts used:
//   "now i want you to improve on it so when clicking 2 an entirely new version
//    of the game is shown with scores nice interface use of 3 birds and a win
//    when the object hits the floor with stars shown based on how many brids
//    where used 0 to 3 stars, and sound effects [...] and also make objects
//    destroyale"
//   "for the new version make the ui more modern more facinating and concistent,
//    also make it that a tutorial is shown when starting and also that it is not
//    that pixelated as of now"
// ============================================================================

function init2() {

    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext("2d");
    var W = VIEW_W, H = VIEW_H;           // logical size, see shell.js
    var scale = 30;                       // 1 meter = 30 pixels
    var DT = 1 / 60;                      // time step of the simulation

    // shortcuts to box2d classes
    var Vec2 = Box2D.Common.Math.b2Vec2;
    var BodyDef = Box2D.Dynamics.b2BodyDef;
    var Body = Box2D.Dynamics.b2Body;
    var FixtureDef = Box2D.Dynamics.b2FixtureDef;
    var World = Box2D.Dynamics.b2World;
    var Polygon = Box2D.Collision.Shapes.b2PolygonShape;
    var Circle = Box2D.Collision.Shapes.b2CircleShape;
    var ContactListener = Box2D.Dynamics.b2ContactListener;

    // ---------- gameplay constants ----------
    var GROUND_TOP = 410;
    var SLING_X = 150, SLING_Y = 300;     // where the bird waits on the slingshot
    var BIRD_R = 18, PIG_R = 22;
    var PULL_TO_SPEED = 5.2;              // launch speed (m/s) per meter of pull
    var MAX_PULL = 100;                   // maximum pull in pixels
    var NB_BIRDS = 3;

    // Materials of the blocks: physics, how much damage they take, points, look
    var MATERIALS = {
        wood: { density: 0.6, friction: 0.7, health: 40, points: 500, color: "#d08a3c" },
        ice:  { density: 0.5, friction: 0.2, health: 22, points: 300, color: "#a5e1f5" },
        rock: { density: 1.6, friction: 0.8, health: 80, points: 800, color: "#9ca3af" }
    };
    // impulses smaller than this do no damage (blocks resting on each other)
    var DAMAGE_THRESHOLD = 2.5;

    // ---------- design system: one font, one palette, one panel style ----------
    var FONT = "'Segoe UI', system-ui, -apple-system, Roboto, 'Helvetica Neue', Arial, sans-serif";
    var C = {
        glass: "rgba(15, 23, 42, 0.55)",          // panels
        glassStrong: "rgba(15, 23, 42, 0.82)",    // cards (tutorial, end screen)
        stroke: "rgba(255, 255, 255, 0.16)",      // thin panel border
        soft: "rgba(255, 255, 255, 0.08)",        // inner boxes
        text: "#f8fafc",
        muted: "rgba(226, 232, 240, 0.72)",
        accent: "#fbbf24",                        // amber: primary color
        accentDark: "#f59e0b",
        success: "#34d399",
        danger: "#f87171",
        shadow: "rgba(2, 6, 23, 0.35)"
    };

    var imageFiles = {
        bird: "sprites/red.png", pig: "sprites/target.png",
        wood_bar: "materials/wood_bar.png", ice_bar: "materials/ice_bar.png", rock_bar: "materials/rock_bar.png",
        wood_box: "materials/wood_box.png", ice_box: "materials/ice_box.png", rock_box: "materials/rock_box.png",
        wood_ball: "materials/wood_ball.png", ice_ball: "materials/ice_ball.png", rock_ball: "materials/rock_ball.png"
    };
    var images = {};

    // ---------- state ----------
    var active = false, looping = false;
    var world, blocks, pig, bird;
    var birdsLeft, birdsUsed, score, shownScore, best = loadBest();
    var totalBlocks, broken;
    var state;            // "aim", "flying", "next", "last", "won-wait", "won", "lost"
    var drag;             // { x, y } pulled position of the bird, in pixels
    var flyTime, slowTime, waitTimer, endTime;
    var pigDown, stars;
    var toDestroy, particles, popups;
    var tutorial = { open: false, step: 0, since: 0 };
    var hover = { x: -1, y: -1 };
    var buttons = [];     // clickable areas of the last frame
    var time = 0;
    var clouds = [];
    for (var c = 0; c < 6; c++) clouds.push({ x: Math.random() * W, y: 40 + Math.random() * 110, s: 0.6 + Math.random() * 0.8 });

    // ---------- best score, kept in the browser ----------
    function loadBest() {
        try { return parseInt(localStorage.getItem("angrybirds-v2-best"), 10) || 0; } catch (e) { return 0; }
    }
    function saveBest() {
        try { localStorage.setItem("angrybirds-v2-best", String(best)); } catch (e) { }
    }

    // ------------------------------------------------------------------------
    // Bodies
    // ------------------------------------------------------------------------
    function fixture(density, friction, restitution, shape) {
        var f = new FixtureDef();
        f.density = density;
        f.friction = friction;
        f.restitution = restitution;
        f.shape = shape;
        return f;
    }

    function boxShape(w, h) {
        var s = new Polygon();
        s.SetAsBox(w / 2 / scale, h / 2 / scale);   // half sizes, in meters
        return s;
    }

    function addStatic(x, y, w, h, name) {
        var def = new BodyDef();
        def.type = Body.b2_staticBody;
        def.position.Set(x / scale, y / scale);
        var body = world.CreateBody(def);
        body.CreateFixture(fixture(1, 0.8, 0.1, boxShape(w, h)));
        body.SetUserData(name);
        return body;
    }

    function addDynamic(x, y, f) {
        var def = new BodyDef();
        def.type = Body.b2_dynamicBody;
        def.position.Set(x / scale, y / scale);
        var body = world.CreateBody(def);
        body.CreateFixture(f);
        return body;
    }

    // random crack lines (in a -0.5..0.5 square), drawn when a block is damaged
    function makeCracks() {
        var lines = [];
        for (var i = 0; i < 6; i++) {
            var x = Math.random() - 0.5, y = Math.random() - 0.5, pts = [[x, y]];
            for (var k = 0; k < 3; k++) {
                x += (Math.random() - 0.5) * 0.5;
                y += (Math.random() - 0.5) * 0.5;
                pts.push([Math.max(-0.5, Math.min(0.5, x)), Math.max(-0.5, Math.min(0.5, y))]);
            }
            lines.push(pts);
        }
        return lines;
    }

    // a destroyable block. kind: "bar" (w x h, vertical = standing), "box" (w x w), "ball" (radius w)
    function addBlock(material, kind, x, y, w, h, vertical) {
        var m = MATERIALS[material];
        var block = { material: material, kind: kind, health: m.health, maxHealth: m.health,
                      cracks: makeCracks(), vertical: !!vertical };
        if (kind === "ball") {
            block.body = addDynamic(x, y, fixture(m.density, m.friction, 0.2, new Circle(w / scale)));
            block.dw = block.dh = 2 * w;
            block.img = images[material + "_ball"];
        } else {
            block.body = addDynamic(x, y, fixture(m.density, m.friction, 0.1, boxShape(w, h)));
            block.dw = vertical ? h : w;       // image size once turned back to horizontal
            block.dh = vertical ? w : h;
            block.img = images[material + "_" + kind];
        }
        block.body.SetUserData({ block: block });
        blocks.push(block);
    }

    function addBird() {
        bird = addDynamic(SLING_X, SLING_Y, fixture(2, 0.6, 0.3, new Circle(BIRD_R / scale)));
        bird.SetUserData("bird");
        bird.SetBullet(true);                  // continuous collision: a fast bird does not pass through thin bars
        state = "aim";
        Sound.newBird();
    }

    // ------------------------------------------------------------------------
    // Level
    // ------------------------------------------------------------------------
    function buildScene() {
        world = new World(new Vec2(0, 10), true);
        blocks = [];
        toDestroy = [];
        particles = [];
        popups = [];
        drag = null;
        bird = null;
        birdsLeft = NB_BIRDS;
        birdsUsed = 0;
        score = 0;
        shownScore = 0;
        broken = 0;
        pigDown = false;
        stars = 0;
        waitTimer = 0;

        // ground and side walls (static)
        addStatic(W / 2, GROUND_TOP + 20, W, 40, "ground");
        addStatic(0, 0, 20, 2 * H, "wall");
        addStatic(W, 0, 20, 2 * H, "wall");

        // two-floor fortress
        addBlock("rock", "box", 440, 386, 48, 48);                 // guard in front
        addBlock("wood", "bar", 500, 360, 14, 100, true);          // ground floor, left part
        addBlock("wood", "bar", 580, 360, 14, 100, true);
        addBlock("wood", "box", 540, 387, 46, 46);
        addBlock("wood", "bar", 540, 303, 120, 14);
        addBlock("ice", "bar", 620, 360, 14, 100, true);           // ground floor, right part
        addBlock("ice", "bar", 700, 360, 14, 100, true);
        addBlock("ice", "box", 660, 387, 46, 46);
        addBlock("ice", "bar", 660, 303, 120, 14);
        addBlock("wood", "bar", 560, 261, 14, 70, true);           // first floor
        addBlock("wood", "bar", 640, 261, 14, 70, true);
        addBlock("rock", "bar", 600, 219, 110, 14);                // roof
        addBlock("rock", "ball", 495, 283, 13);                    // balls on the planks
        addBlock("ice", "ball", 705, 283, 13);
        totalBlocks = blocks.length;

        // the pig on the roof
        pig = addDynamic(600, 219 - 7 - PIG_R, fixture(1, 0.6, 0.2, new Circle(PIG_R / scale)));
        pig.SetUserData("target");

        // contacts
        var listener = new ContactListener();
        listener.BeginContact = function (contact) {
            var a = contact.GetFixtureA().GetBody().GetUserData();
            var b = contact.GetFixtureB().GetBody().GetUserData();
            // WIN: the pig touches the ground
            if (!pigDown && ((a === "target" && b === "ground") || (a === "ground" && b === "target"))) {
                pigDown = true;
            }
        };
        // after the solver: the impulse tells how hard two bodies hit each other
        listener.PostSolve = function (contact, impulse) {
            var imp = impulse.normalImpulses[0];
            if (impulse.normalImpulses[1]) imp = Math.max(imp, impulse.normalImpulses[1]);
            if (imp < DAMAGE_THRESHOLD) return;
            var a = contact.GetFixtureA().GetBody().GetUserData();
            var b = contact.GetFixtureB().GetBody().GetUserData();
            damage(a, imp);
            damage(b, imp);
            if (imp > 3) Sound.hit(imp);
        };
        world.SetContactListener(listener);

        addBird();
    }

    // points are only counted while the game is running (not after the end card)
    function ended() { return state === "won" || state === "lost"; }
    function addScore(n) {
        if (!ended()) score += n;
    }

    // a block loses health. It is destroyed after the Step (never inside a callback)
    function damage(data, imp) {
        if (!data || !data.block) return;
        var block = data.block;
        if (block.health <= 0) return;
        var d = imp - DAMAGE_THRESHOLD;
        block.health -= d;
        addScore(Math.round(d * 10));
        if (block.health <= 0) toDestroy.push(block);
    }

    function destroyBlock(block) {
        var p = block.body.GetPosition();
        var x = p.x * scale, y = p.y * scale;
        world.DestroyBody(block.body);
        blocks.splice(blocks.indexOf(block), 1);
        var pts = MATERIALS[block.material].points;
        if (!ended()) {
            broken++;
            addScore(pts);
            popups.push({ x: x, y: y, text: "+" + pts, life: 1.2, color: C.text });
        }
        burst(x, y, MATERIALS[block.material].color, 16);
        Sound.breakBlock(block.material);
    }

    function burst(x, y, color, n) {
        for (var i = 0; i < n; i++) {
            particles.push({ x: x, y: y, vx: (Math.random() - 0.5) * 300, vy: -Math.random() * 250,
                             life: 0.6 + Math.random() * 0.5, size: 3 + Math.random() * 5,
                             rot: Math.random() * 6, color: color });
        }
    }

    // ------------------------------------------------------------------------
    // Tutorial
    // ------------------------------------------------------------------------
    var TUTORIAL = [
        { title: "Pull back the bird",
          text: "Press on the red bird and drag it backwards. The further you pull, the stronger the shot." },
        { title: "Aim and release",
          text: "The dotted line shows where the bird will fly and the ring shows the power. Release the mouse to launch." },
        { title: "Break the fortress",
          text: "Blocks crack and then break when they are hit hard. Ice is fragile, wood is medium and rock is the toughest." },
        { title: "Knock the pig to the ground",
          text: "The level is won as soon as the pig touches the ground. You have 3 birds: the fewer you use, the more stars you get." }
    ];

    function openTutorial() {
        tutorial.open = true;
        tutorial.step = 0;
        tutorial.since = time;
        drag = null;
    }
    function tutorialNext() {
        if (tutorial.step < TUTORIAL.length - 1) { tutorial.step++; tutorial.since = time; Sound.newBird(); }
        else closeTutorial();
    }
    function tutorialBack() {
        if (tutorial.step > 0) { tutorial.step--; tutorial.since = time; }
    }
    function closeTutorial() {
        tutorial.open = false;
        Sound.stretch();
    }

    // ------------------------------------------------------------------------
    // Input
    // ------------------------------------------------------------------------
    function inside(p, b) { return p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h; }

    function buttonAt(p) {
        for (var i = buttons.length - 1; i >= 0; i--) if (inside(p, buttons[i])) return buttons[i];
        return null;
    }

    function nearBird(p) {
        var dx = p.x - SLING_X, dy = p.y - SLING_Y;
        return dx * dx + dy * dy <= (BIRD_R + 14) * (BIRD_R + 14);
    }

    canvas.addEventListener("mousedown", function (e) {
        if (!active) return;
        var p = canvasPoint(e);
        var b = buttonAt(p);
        if (b) { b.onClick(); return; }
        if (tutorial.open || state !== "aim") return;
        if (nearBird(p)) {
            drag = { x: SLING_X, y: SLING_Y };
            Sound.stretch();
        }
    });

    document.addEventListener("mousemove", function (e) {
        if (!active) return;
        var p = canvasPoint(e);
        hover = p;
        if (drag) {
            var dx = p.x - SLING_X, dy = p.y - SLING_Y;
            var len = Math.sqrt(dx * dx + dy * dy);
            if (len > MAX_PULL) { dx *= MAX_PULL / len; dy *= MAX_PULL / len; }
            drag.x = SLING_X + dx;
            drag.y = Math.min(SLING_Y + dy, GROUND_TOP - BIRD_R);
        }
        // mouse cursor: hand on buttons, grab on the bird
        var cursor = "default";
        if (drag) cursor = "grabbing";
        else if (buttonAt(p)) cursor = "pointer";
        else if (!tutorial.open && state === "aim" && nearBird(p)) cursor = "grab";
        canvas.style.cursor = cursor;
    });

    document.addEventListener("mouseup", function () {
        if (!active || !drag) return;
        var v = launchVelocity();
        drag = null;
        if (v.x * v.x + v.y * v.y < 4) return;     // pulled too little: the bird stays on the slingshot
        bird.SetLinearVelocity(new Vec2(v.x, v.y));
        state = "flying";
        flyTime = 0;
        slowTime = 0;
        birdsLeft--;
        birdsUsed++;
        Sound.launch();
    });

    // speed given to the bird (m/s): opposite to the pull, proportional to its length
    function launchVelocity() {
        return { x: (SLING_X - drag.x) / scale * PULL_TO_SPEED, y: (SLING_Y - drag.y) / scale * PULL_TO_SPEED };
    }

    document.addEventListener("keydown", function (e) {
        if (!active) return;
        if (tutorial.open) {
            if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") { tutorialNext(); e.preventDefault(); }
            if (e.key === "ArrowLeft") tutorialBack();
            if (e.key === "Escape") closeTutorial();
            return;
        }
        if (e.key === "r" || e.key === "R") buildScene();
        if (e.key === "m" || e.key === "M") Sound.toggleMute();
        if (e.key === "h" || e.key === "H") openTutorial();
    });

    // ------------------------------------------------------------------------
    // Update
    // ------------------------------------------------------------------------
    function update() {
        time += DT;
        clouds.forEach(function (cl) { cl.x += 8 * cl.s * DT; if (cl.x > W + 80) cl.x = -80; });
        shownScore += (score - shownScore) * 0.12;            // the score counts up smoothly
        if (Math.abs(score - shownScore) < 1) shownScore = score;
        if (tutorial.open) return;                             // the game is paused during the tutorial

        // the bird stays on the slingshot (or under the mouse) until it is launched
        if (state === "aim" && bird) {
            var hx = drag ? drag.x : SLING_X, hy = drag ? drag.y : SLING_Y;
            bird.SetPosition(new Vec2(hx / scale, hy / scale));
            bird.SetLinearVelocity(new Vec2(0, 0));
            bird.SetAngularVelocity(0);
            bird.SetAwake(true);
        }

        world.Step(DT, 10, 10);
        world.ClearForces();

        // destroy the broken blocks (after the Step)
        for (var i = 0; i < toDestroy.length; i++) {
            if (blocks.indexOf(toDestroy[i]) >= 0) destroyBlock(toDestroy[i]);
        }
        toDestroy = [];

        // the pig fell on the ground: points now, win card a moment later
        if (pigDown && !ended() && state !== "won-wait") {
            var pp = pig.GetPosition();
            addScore(5000);
            popups.push({ x: pp.x * scale, y: pp.y * scale - 30, text: "+5000", life: 1.5, color: C.accent });
            burst(pp.x * scale, pp.y * scale, "#7cc142", 20);
            Sound.pig();
            state = "won-wait";
            waitTimer = 1.2;
        }

        // the flying bird is finished when it stops moving or after 8 seconds
        if (state === "flying") {
            flyTime += DT;
            var v = bird.GetLinearVelocity();
            if (v.x * v.x + v.y * v.y < 0.1) slowTime += DT; else slowTime = 0;
            if (slowTime > 1 || flyTime > 8) {
                removeBird();
                if (birdsLeft > 0) { state = "next"; waitTimer = 0.6; }
                else { state = "last"; waitTimer = 2.5; }      // let the fortress settle before losing
            }
        }

        if (waitTimer > 0) {
            waitTimer -= DT;
            if (waitTimer <= 0) {
                if (state === "next") addBird();
                else if (state === "last") endGame(false);
                else if (state === "won-wait") endGame(true);
            }
        }

        // particles and score pop-ups
        for (var p = particles.length - 1; p >= 0; p--) {
            var q = particles[p];
            q.vy += 600 * DT;
            q.x += q.vx * DT;
            q.y += q.vy * DT;
            q.rot += 5 * DT;
            q.life -= DT;
            if (q.life <= 0) particles.splice(p, 1);
        }
        for (var k = popups.length - 1; k >= 0; k--) {
            popups[k].y -= 40 * DT;
            popups[k].life -= DT;
            if (popups[k].life <= 0) popups.splice(k, 1);
        }
    }

    function removeBird() {
        if (!bird) return;
        var p = bird.GetPosition();
        burst(p.x * scale, p.y * scale, "#fff", 12);
        world.DestroyBody(bird);
        bird = null;
        Sound.poof();
    }

    // stars: 1 bird used = 3 stars, 2 birds = 2 stars, 3 birds = 1 star, pig alive = 0 stars
    function endGame(win) {
        if (win) {
            stars = Math.max(1, Math.min(3, NB_BIRDS + 1 - birdsUsed));
            score += birdsLeft * 10000;                // each unused bird is worth 10000 points
            Sound.win();
            for (var i = 0; i < stars; i++) Sound.star(i, 0.6 + i * 0.35);
        } else {
            stars = 0;
            Sound.lose();
        }
        state = win ? "won" : "lost";
        endTime = time;
        if (score > best) { best = score; saveBest(); }
    }

    // ------------------------------------------------------------------------
    // Drawing helpers (design system)
    // ------------------------------------------------------------------------
    // shadows are not scaled by the transform: multiply by the canvas resolution
    function px(n) { return n * canvas.width / W; }

    function roundRect(x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }

    function text(str, x, y, size, color, align, weight, baseline) {
        ctx.font = (weight || 600) + " " + size + "px " + FONT;
        ctx.fillStyle = color;
        ctx.textAlign = align || "left";
        ctx.textBaseline = baseline || "alphabetic";
        ctx.fillText(str, x, y);
    }

    function shadow(blur, offsetY, color) {
        ctx.shadowColor = color || C.shadow;
        ctx.shadowBlur = px(blur);
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = px(offsetY || 0);
    }

    // glass panel: dark translucent, rounded, soft shadow, thin light border
    function glass(x, y, w, h, r, fill) {
        ctx.save();
        shadow(18, 6);
        roundRect(x, y, w, h, r);
        ctx.fillStyle = fill || C.glass;
        ctx.fill();
        ctx.restore();
        roundRect(x + 0.5, y + 0.5, w - 1, h - 1, r);
        ctx.strokeStyle = C.stroke;
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // registers a clickable area, returns true when the mouse is over it
    function clickable(x, y, w, h, onClick) {
        var b = { x: x, y: y, w: w, h: h, onClick: onClick };
        buttons.push(b);
        return inside(hover, b);
    }

    function pillButton(label, x, y, w, h, primary, onClick) {
        var over = clickable(x, y, w, h, onClick);
        ctx.save();
        if (primary) shadow(14, 4, "rgba(245, 158, 11, 0.45)");
        roundRect(x, y, w, h, h / 2);
        if (primary) {
            var g = ctx.createLinearGradient(x, y, x, y + h);
            g.addColorStop(0, over ? "#fde68a" : "#fcd34d");
            g.addColorStop(1, over ? C.accent : C.accentDark);
            ctx.fillStyle = g;
        } else {
            ctx.fillStyle = over ? "rgba(255, 255, 255, 0.22)" : "rgba(255, 255, 255, 0.1)";
        }
        ctx.fill();
        ctx.restore();
        if (!primary) {
            roundRect(x + 0.5, y + 0.5, w - 1, h - 1, h / 2);
            ctx.strokeStyle = C.stroke;
            ctx.lineWidth = 1;
            ctx.stroke();
        }
        text(label, x + w / 2, y + h / 2 + 1, 14, primary ? "#1f2937" : C.text, "center", 700, "middle");
    }

    // round icon button (restart, sound, fullscreen, help)
    function iconButton(icon, x, y, size, onClick) {
        var over = clickable(x, y, size, size, onClick);
        ctx.save();
        shadow(12, 4);
        ctx.beginPath();
        ctx.arc(x + size / 2, y + size / 2, size / 2, 0, 2 * Math.PI);
        ctx.fillStyle = over ? "rgba(30, 41, 59, 0.85)" : C.glass;
        ctx.fill();
        ctx.restore();
        ctx.beginPath();
        ctx.arc(x + size / 2, y + size / 2, size / 2 - 0.5, 0, 2 * Math.PI);
        ctx.strokeStyle = over ? "rgba(251, 191, 36, 0.8)" : C.stroke;
        ctx.lineWidth = 1;
        ctx.stroke();
        drawIcon(icon, x + size / 2, y + size / 2, size * 0.26, over ? C.accent : C.text);
    }

    function drawIcon(icon, cx, cy, s, color) {
        ctx.save();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        if (icon === "restart") {
            ctx.arc(cx, cy, s, -0.3, Math.PI * 1.55);
            ctx.stroke();
            ctx.beginPath();                                   // arrow head
            ctx.moveTo(cx + s * 1.05, cy - s * 0.95);
            ctx.lineTo(cx + s * 0.98, cy - s * 0.1);
            ctx.lineTo(cx + s * 0.2, cy - s * 0.45);
            ctx.stroke();
        } else if (icon === "sound" || icon === "muted") {
            ctx.moveTo(cx - s, cy - s * 0.4);                  // speaker
            ctx.lineTo(cx - s * 0.45, cy - s * 0.4);
            ctx.lineTo(cx + s * 0.15, cy - s);
            ctx.lineTo(cx + s * 0.15, cy + s);
            ctx.lineTo(cx - s * 0.45, cy + s * 0.4);
            ctx.lineTo(cx - s, cy + s * 0.4);
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            if (icon === "sound") {
                ctx.arc(cx + s * 0.3, cy, s * 0.55, -0.9, 0.9);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(cx + s * 0.3, cy, s * 1.05, -0.9, 0.9);
            } else {
                ctx.moveTo(cx + s * 0.5, cy - s * 0.45);
                ctx.lineTo(cx + s * 1.25, cy + s * 0.45);
                ctx.moveTo(cx + s * 1.25, cy - s * 0.45);
                ctx.lineTo(cx + s * 0.5, cy + s * 0.45);
            }
            ctx.stroke();
        } else if (icon === "fullscreen") {
            var a = s, b = s * 0.45;                           // four corners
            ctx.moveTo(cx - a, cy - a + b); ctx.lineTo(cx - a, cy - a); ctx.lineTo(cx - a + b, cy - a);
            ctx.moveTo(cx + a - b, cy - a); ctx.lineTo(cx + a, cy - a); ctx.lineTo(cx + a, cy - a + b);
            ctx.moveTo(cx + a, cy + a - b); ctx.lineTo(cx + a, cy + a); ctx.lineTo(cx + a - b, cy + a);
            ctx.moveTo(cx - a + b, cy + a); ctx.lineTo(cx - a, cy + a); ctx.lineTo(cx - a, cy + a - b);
            ctx.stroke();
        } else if (icon === "help") {
            ctx.font = "800 " + (s * 2.2) + "px " + FONT;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("?", cx, cy + 1);
        }
        ctx.restore();
    }

    function drawStar(cx, cy, r, filled, pop) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(pop, pop);
        ctx.beginPath();
        for (var i = 0; i < 10; i++) {
            var a = -Math.PI / 2 + i * Math.PI / 5;
            var rr = i % 2 === 0 ? r : r * 0.48;
            ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
        }
        ctx.closePath();
        if (filled) {
            shadow(22, 0, "rgba(251, 191, 36, 0.8)");
            var g = ctx.createLinearGradient(0, -r, 0, r);
            g.addColorStop(0, "#fde68a");
            g.addColorStop(1, C.accentDark);
            ctx.fillStyle = g;
            ctx.fill();
        } else {
            ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
            ctx.fill();
            ctx.strokeStyle = "rgba(255, 255, 255, 0.28)";
            ctx.lineWidth = 2;
            ctx.stroke();
        }
        ctx.restore();
    }

    // text on several lines
    function wrap(str, x, y, maxW, lineH, size, color, align) {
        ctx.font = "500 " + size + "px " + FONT;
        var words = str.split(" "), line = "", lines = [];
        for (var i = 0; i < words.length; i++) {
            var test = line ? line + " " + words[i] : words[i];
            if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = words[i]; }
            else line = test;
        }
        lines.push(line);
        for (var k = 0; k < lines.length; k++) text(lines[k], x, y + k * lineH, size, color, align, 500);
    }

    // ------------------------------------------------------------------------
    // Scene
    // ------------------------------------------------------------------------
    function drawBackground() {
        var sky = ctx.createLinearGradient(0, 0, 0, GROUND_TOP);
        sky.addColorStop(0, "#3b82f6");
        sky.addColorStop(0.55, "#93c5fd");
        sky.addColorStop(1, "#fde68a");
        ctx.fillStyle = sky;
        ctx.fillRect(0, 0, W, H);

        // sun with a soft glow
        var glow = ctx.createRadialGradient(470, 150, 10, 470, 150, 150);
        glow.addColorStop(0, "rgba(255, 247, 214, 0.95)");
        glow.addColorStop(0.25, "rgba(254, 240, 138, 0.45)");
        glow.addColorStop(1, "rgba(254, 240, 138, 0)");
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = "#fffbeb";
        ctx.beginPath(); ctx.arc(470, 150, 26, 0, 2 * Math.PI); ctx.fill();

        // clouds
        ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
        clouds.forEach(function (cl) {
            ctx.beginPath();
            ctx.arc(cl.x, cl.y, 16 * cl.s, 0, 2 * Math.PI);
            ctx.arc(cl.x + 18 * cl.s, cl.y - 9 * cl.s, 20 * cl.s, 0, 2 * Math.PI);
            ctx.arc(cl.x + 38 * cl.s, cl.y, 16 * cl.s, 0, 2 * Math.PI);
            ctx.rect(cl.x, cl.y, 38 * cl.s, 16 * cl.s);
            ctx.fill();
        });

        // three layers of landscape, far (hazy) to near (green)
        layer(["#c7d2fe", "#a5b4fc"], 300, [[0, 70], [120, 30], [230, 85], [360, 20], [470, 75], [600, 35], [720, 80], [800, 45]]);
        hills(["#bbf7d0", "#86efac"], 352, 26, 0.009, 1.3);
        hills(["#86efac", "#4ade80"], 378, 18, 0.016, 0.2);

        // ground: grass then soil
        var soil = ctx.createLinearGradient(0, GROUND_TOP, 0, H);
        soil.addColorStop(0, "#92400e");
        soil.addColorStop(1, "#451a03");
        ctx.fillStyle = soil;
        ctx.fillRect(0, GROUND_TOP, W, H - GROUND_TOP);
        var grass = ctx.createLinearGradient(0, GROUND_TOP - 4, 0, GROUND_TOP + 12);
        grass.addColorStop(0, "#4ade80");
        grass.addColorStop(1, "#15803d");
        ctx.fillStyle = grass;
        ctx.beginPath();
        ctx.moveTo(0, GROUND_TOP + 12);
        ctx.lineTo(0, GROUND_TOP);
        for (var x = 0; x < W; x += 16) ctx.quadraticCurveTo(x + 8, GROUND_TOP - 6, x + 16, GROUND_TOP);
        ctx.lineTo(W, GROUND_TOP + 12);
        ctx.closePath();
        ctx.fill();
    }

    // mountains: polygon through the given points (x, height above "base")
    function layer(colors, base, pts) {
        var g = ctx.createLinearGradient(0, base - 90, 0, GROUND_TOP);
        g.addColorStop(0, colors[0]);
        g.addColorStop(1, colors[1]);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.moveTo(0, GROUND_TOP);
        pts.forEach(function (p) { ctx.lineTo(p[0], base - p[1]); });
        ctx.lineTo(W, GROUND_TOP);
        ctx.closePath();
        ctx.fill();
    }

    function hills(colors, base, amp, freq, phase) {
        var g = ctx.createLinearGradient(0, base - 2 * amp, 0, GROUND_TOP);
        g.addColorStop(0, colors[0]);
        g.addColorStop(1, colors[1]);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.moveTo(0, GROUND_TOP);
        for (var x = 0; x <= W; x += 8) ctx.lineTo(x, base - amp * Math.sin(x * freq + phase) - amp);
        ctx.lineTo(W, GROUND_TOP);
        ctx.closePath();
        ctx.fill();
    }

    function drawWalls() {
        ctx.fillStyle = "rgba(15, 23, 42, 0.55)";
        ctx.fillRect(0, 0, 10, H);
        ctx.fillRect(W - 10, 0, 10, H);
    }

    // a sprite on its body: follows the position and the rotation, with a soft shadow
    function drawOnBody(body, img, dw, dh, vertical) {
        var p = body.GetPosition();
        ctx.save();
        shadow(6, 3, "rgba(15, 23, 42, 0.3)");
        ctx.translate(p.x * scale, p.y * scale);
        ctx.rotate(body.GetAngle());
        if (vertical) ctx.rotate(Math.PI / 2);
        ctx.drawImage(img, -dw / 2, -dh / 2, dw, dh);
        ctx.restore();
    }

    function drawBlock(b) {
        drawOnBody(b.body, b.img, b.dw, b.dh, b.vertical);
        // cracks: half of them below 66% health, all of them below 33%
        var ratio = b.health / b.maxHealth;
        if (ratio > 0.66) return;
        var n = ratio > 0.33 ? 3 : 6;
        var p = b.body.GetPosition();
        ctx.save();
        ctx.translate(p.x * scale, p.y * scale);
        ctx.rotate(b.body.GetAngle());
        if (b.vertical) ctx.rotate(Math.PI / 2);
        ctx.strokeStyle = "rgba(30, 15, 0, 0.75)";
        ctx.lineWidth = 1.4;
        ctx.lineJoin = "round";
        for (var i = 0; i < n; i++) {
            var pts = b.cracks[i];
            ctx.beginPath();
            ctx.moveTo(pts[0][0] * b.dw, pts[0][1] * b.dh);
            for (var k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0] * b.dw, pts[k][1] * b.dh);
            ctx.stroke();
        }
        ctx.restore();
    }

    // slingshot: Y-shaped, wood colors, rubber bands behind and in front of the bird
    function prong(x1, y1, x2, y2, color) {
        ctx.strokeStyle = color;
        ctx.lineCap = "round";
        ctx.lineWidth = 9;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }

    function drawSlingshotBack() {
        ctx.save();
        shadow(8, 3, "rgba(15, 23, 42, 0.3)");
        prong(SLING_X, GROUND_TOP, SLING_X, SLING_Y + 30, "#7c4a1e");
        prong(SLING_X, SLING_Y + 30, SLING_X + 12, SLING_Y - 6, "#5b3414");
        ctx.restore();
        band(SLING_X + 12, SLING_Y - 6);
    }

    function drawSlingshotFront() {
        band(SLING_X - 12, SLING_Y - 6);
        prong(SLING_X, SLING_Y + 30, SLING_X - 12, SLING_Y - 6, "#8b5a2b");
    }

    function band(x0, y0) {
        ctx.strokeStyle = "#3f1d0b";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        if (state === "aim" && bird) {
            var p = bird.GetPosition();
            ctx.lineTo(p.x * scale - (x0 < SLING_X ? 0 : 6), p.y * scale);
        } else {
            ctx.lineTo(SLING_X, SLING_Y);
        }
        ctx.stroke();
    }

    // aiming: dotted path (no collisions) and a power ring around the bird
    function drawAim() {
        if (!drag) return;
        var v = launchVelocity();
        var x0 = drag.x / scale, y0 = drag.y / scale;
        ctx.save();
        shadow(6, 0, "rgba(255, 255, 255, 0.8)");
        for (var i = 1; i <= 26; i++) {
            var t = i * 0.07;
            var x = (x0 + v.x * t) * scale, y = (y0 + v.y * t + 0.5 * 10 * t * t) * scale;
            if (y > GROUND_TOP || x > W) break;
            ctx.fillStyle = "rgba(255, 255, 255, " + (1 - i / 30) + ")";
            ctx.beginPath(); ctx.arc(x, y, 3.6 - i * 0.08, 0, 2 * Math.PI); ctx.fill();
        }
        ctx.restore();

        var dx = drag.x - SLING_X, dy = drag.y - SLING_Y;
        var power = Math.min(1, Math.sqrt(dx * dx + dy * dy) / MAX_PULL);
        ctx.lineCap = "round";
        ctx.lineWidth = 4;
        ctx.strokeStyle = "rgba(15, 23, 42, 0.35)";
        ctx.beginPath(); ctx.arc(drag.x, drag.y, BIRD_R + 9, 0, 2 * Math.PI); ctx.stroke();
        ctx.strokeStyle = power < 0.7 ? C.accent : "#fb923c";
        ctx.beginPath(); ctx.arc(drag.x, drag.y, BIRD_R + 9, -Math.PI / 2, -Math.PI / 2 + power * 2 * Math.PI); ctx.stroke();
        glass(drag.x - 24, drag.y - BIRD_R - 40, 48, 22, 11);
        text(Math.round(power * 100) + "%", drag.x, drag.y - BIRD_R - 28, 12, C.text, "center", 700, "middle");
    }

    function drawWaitingBirds() {
        // birds still to launch, hopping behind the slingshot
        var waiting = birdsLeft - (state === "aim" ? 1 : 0);
        for (var i = 0; i < waiting; i++) {
            var hop = Math.abs(Math.sin(time * 3 + i)) * 4;
            ctx.drawImage(images.bird, SLING_X - 62 - i * 34, GROUND_TOP - 30 - hop, 30, 30);
        }
    }

    // ------------------------------------------------------------------------
    // Interface
    // ------------------------------------------------------------------------
    function drawHUD() {
        // score card
        glass(16, 14, 196, 60, 16);
        text("SCORE", 32, 34, 11, C.muted, "left", 700);
        text(Math.round(shownScore).toLocaleString("en-US"), 32, 62, 26, C.text, "left", 800);
        text("BEST", 196, 34, 11, C.muted, "right", 700);
        text(best.toLocaleString("en-US"), 196, 52, 13, C.accent, "right", 700);

        // level chip
        glass(W / 2 - 92, 20, 184, 32, 16);
        ctx.drawImage(images.pig, W / 2 - 82, 25, 22, 22);
        text("Level 1 · Pig Fortress", W / 2 + 12, 37, 13, C.text, "center", 700, "middle");

        // birds left, used ones faded
        var bx = W - 16 - 124;
        glass(bx, 14, 124, 44, 22);
        for (var i = 0; i < NB_BIRDS; i++) {
            var cx = bx + 24 + i * 38, cy = 36, left = i < birdsLeft;
            ctx.globalAlpha = left ? 1 : 0.28;
            ctx.beginPath();
            ctx.arc(cx, cy, 16, 0, 2 * Math.PI);
            ctx.fillStyle = left ? "rgba(251, 191, 36, 0.22)" : "rgba(255, 255, 255, 0.08)";
            ctx.fill();
            ctx.strokeStyle = left ? C.accent : C.stroke;
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.drawImage(images.bird, cx - 13, cy - 13, 26, 26);
            ctx.globalAlpha = 1;
        }

        // icon buttons
        var y = 66, s = 32, x0 = W - 16 - 4 * s - 3 * 8;
        iconButton("restart", x0, y, s, function () { buildScene(); });
        iconButton(Sound.isMuted() ? "muted" : "sound", x0 + (s + 8), y, s, function () { Sound.toggleMute(); });
        iconButton("fullscreen", x0 + 2 * (s + 8), y, s, function () { toggleFullscreen(); });
        iconButton("help", x0 + 3 * (s + 8), y, s, function () { openTutorial(); });

        // hint before the first launch
        if (state === "aim" && birdsUsed === 0 && !drag && !tutorial.open) {
            ctx.globalAlpha = 0.65 + 0.35 * Math.sin(time * 3);
            glass(W / 2 - 120, H - 52, 240, 32, 16);
            text("Drag the bird back and release", W / 2, H - 35, 13, C.text, "center", 600, "middle");
            ctx.globalAlpha = 1;
        }
    }

    function drawPopups() {
        popups.forEach(function (pp) {
            ctx.save();
            ctx.globalAlpha = Math.min(1, pp.life * 2);
            shadow(8, 2, "rgba(15, 23, 42, 0.6)");
            text(pp.text, pp.x, pp.y, 18, pp.color, "center", 800, "middle");
            ctx.restore();
        });
    }

    function dim(alpha) {
        ctx.fillStyle = "rgba(2, 6, 23, " + alpha + ")";
        ctx.fillRect(0, 0, W, H);
    }

    // card at the end: stars, score, stats, buttons
    function drawEndCard() {
        if (!ended()) return;
        buttons = [];                                          // only the card's buttons are clickable
        var t = time - endTime;
        var appear = Math.min(1, t / 0.35);
        dim(0.55 * appear);

        var cw = 420, ch = 280, cx = (W - cw) / 2, cy = 52 + (1 - appear) * 20;
        ctx.globalAlpha = appear;
        glass(cx, cy, cw, ch, 24, C.glassStrong);

        var won = state === "won";
        glass(W / 2 - 46, cy + 18, 92, 24, 12, C.soft);
        text("LEVEL 1", W / 2, cy + 31, 11, C.muted, "center", 700, "middle");
        text(won ? "Level cleared!" : "The pig survived", W / 2, cy + 74, 28, won ? C.success : C.danger, "center", 800);

        // stars pop in one after the other
        for (var i = 0; i < 3; i++) {
            var start = 0.6 + i * 0.35, on = i < stars && t > start;
            var pop = on ? Math.min(1, (t - start) / 0.2) * (1 + 0.25 * Math.max(0, 1 - (t - start) / 0.3)) : 1;
            drawStar(W / 2 + (i - 1) * 74, cy + 122 - (i === 1 ? 10 : 0), i === 1 ? 32 : 26, on, pop);
        }

        text("SCORE", W / 2, cy + 172, 11, C.muted, "center", 700);
        text(Math.round(shownScore).toLocaleString("en-US"), W / 2, cy + 204, 30, C.text, "center", 800);

        // three small stats
        var stats = [["Birds used", birdsUsed + " / " + NB_BIRDS], ["Blocks broken", broken + " / " + totalBlocks],
                     ["Best", best.toLocaleString("en-US")]];
        for (var k = 0; k < 3; k++) {
            var sx = cx + 24 + k * 128;
            glass(sx, cy + 224, 116, 38, 10, C.soft);
            text(stats[k][0], sx + 58, cy + 237, 10, C.muted, "center", 600, "middle");
            text(stats[k][1], sx + 58, cy + 251, 12, C.text, "center", 700, "middle");
        }

        pillButton("Play again  (R)", W / 2 - 160, cy + ch + 14, 180, 38, true, function () { buildScene(); });
        pillButton("Classic  (1)", W / 2 + 32, cy + ch + 14, 128, 38, false, function () { switchVersion(1); });
        ctx.globalAlpha = 1;
    }

    // tutorial card with an animated illustration for each step
    function drawTutorial() {
        if (!tutorial.open) return;
        buttons = [];
        var t = time - tutorial.since;
        var appear = Math.min(1, t / 0.25);
        dim(0.55);

        var cw = 540, ch = 330, cx = (W - cw) / 2, cy = (H - ch) / 2 - 12;
        glass(cx, cy, cw, ch, 24, C.glassStrong);

        // illustration area
        var ix = cx + 20, iy = cy + 20, iw = cw - 40, ih = 120;
        ctx.save();
        roundRect(ix, iy, iw, ih, 16);
        ctx.clip();
        var g = ctx.createLinearGradient(0, iy, 0, iy + ih);
        g.addColorStop(0, "#60a5fa");
        g.addColorStop(1, "#fde68a");
        ctx.fillStyle = g;
        ctx.fillRect(ix, iy, iw, ih);
        ctx.fillStyle = "#22c55e";
        ctx.fillRect(ix, iy + ih - 18, iw, 18);
        ctx.globalAlpha = appear;
        drawIllustration(tutorial.step, ix, iy, iw, ih, t);
        ctx.restore();
        roundRect(ix + 0.5, iy + 0.5, iw - 1, ih - 1, 16);
        ctx.strokeStyle = C.stroke;
        ctx.lineWidth = 1;
        ctx.stroke();

        // step, title, text
        var step = TUTORIAL[tutorial.step];
        text("STEP " + (tutorial.step + 1) + " OF " + TUTORIAL.length, cx + 28, cy + 168, 11, C.accent, "left", 800);
        text(step.title, cx + 28, cy + 198, 22, C.text, "left", 800);
        wrap(step.text, cx + 28, cy + 224, cw - 56, 20, 14, C.muted, "left");

        // progress dots
        for (var i = 0; i < TUTORIAL.length; i++) {
            var on = i === tutorial.step;
            ctx.fillStyle = on ? C.accent : "rgba(255, 255, 255, 0.25)";
            roundRect(W / 2 - 38 + i * 20 - (on ? 4 : 0), cy + ch - 34, on ? 18 : 10, 8, 4);
            ctx.fill();
        }

        // buttons
        var last = tutorial.step === TUTORIAL.length - 1;
        if (tutorial.step > 0) pillButton("Back", cx + 20, cy + ch - 48, 90, 36, false, tutorialBack);
        pillButton(last ? "Let's play!" : "Next", cx + cw - 20 - 130, cy + ch - 48, 130, 36, true, tutorialNext);
        var over = clickable(cx + cw - 70, cy + 158, 50, 20, closeTutorial);
        text("Skip", cx + cw - 28, cy + 168, 12, over ? C.text : C.muted, "right", 700, "middle");

        // keyboard shortcuts under the card
        text("R restart  ·  M sound  ·  F fullscreen  ·  H help  ·  1 classic version",
             W / 2, cy + ch + 20, 12, "rgba(255, 255, 255, 0.85)", "center", 600, "middle");
    }

    function drawIllustration(step, x, y, w, h, t) {
        var gy = y + h - 18;                                    // ground line of the illustration
        if (step === 0 || step === 1) {
            var sx = x + 150;                                   // a small slingshot
            ctx.strokeStyle = "#7c4a1e";
            ctx.lineWidth = 6;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(sx, gy); ctx.lineTo(sx, gy - 34);
            ctx.lineTo(sx - 9, gy - 58); ctx.moveTo(sx, gy - 34); ctx.lineTo(sx + 9, gy - 58);
            ctx.stroke();
        }
        if (step === 0) {
            var pull = 0.5 + 0.5 * Math.sin(t * 2.5);           // the bird goes back and forth
            var bxp = x + 140 - pull * 55, byp = gy - 60 + pull * 22;
            ctx.strokeStyle = "#3f1d0b";
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(x + 141, gy - 58); ctx.lineTo(bxp, byp); ctx.lineTo(x + 159, gy - 58); ctx.stroke();
            ctx.drawImage(images.bird, bxp - 16, byp - 16, 32, 32);
            // arrow showing the pull direction
            ctx.strokeStyle = C.text;
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(x + 300, y + 34); ctx.lineTo(x + 230, y + 62); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x + 230, y + 62); ctx.lineTo(x + 244, y + 50); ctx.moveTo(x + 230, y + 62); ctx.lineTo(x + 246, y + 66); ctx.stroke();
            text("pull back", x + 310, y + 36, 13, C.text, "left", 700, "middle");
        } else if (step === 1) {
            // dotted arc and a bird flying along it
            var x0 = x + 150, y0 = gy - 60;
            for (var i = 1; i < 22; i++) {
                var u = i / 22;
                ctx.fillStyle = "rgba(255, 255, 255, " + (1 - u * 0.6) + ")";
                ctx.beginPath(); ctx.arc(x0 + u * 300, y0 - Math.sin(u * Math.PI) * 55 + u * 30, 3, 0, 2 * Math.PI); ctx.fill();
            }
            var f = (t * 0.45) % 1;
            ctx.drawImage(images.bird, x0 + f * 300 - 15, y0 - Math.sin(f * Math.PI) * 55 + f * 30 - 15, 30, 30);
            ctx.drawImage(images.pig, x + 455, gy - 30, 30, 30);
        } else if (step === 2) {
            // the three materials with their strength
            var mats = [["ice", "Fragile", 0.3], ["wood", "Medium", 0.6], ["rock", "Tough", 1]];
            for (var k = 0; k < 3; k++) {
                var mx = x + 80 + k * 140;
                var wob = (k === 0 && t % 2 < 0.4) ? Math.sin(t * 60) * 2 : 0;
                ctx.drawImage(images[mats[k][0] + "_box"], mx + wob, gy - 70, 46, 46);
                text(mats[k][1], mx + 23, y + 18, 12, C.text, "center", 700, "middle");
                ctx.fillStyle = "rgba(15, 23, 42, 0.35)";
                roundRect(mx - 6, gy - 14, 58, 6, 3); ctx.fill();
                ctx.fillStyle = C.accent;
                roundRect(mx - 6, gy - 14, 58 * mats[k][2], 6, 3); ctx.fill();
            }
        } else if (step === 3) {
            // the pig falls, and the stars legend
            var fall = Math.min(1, (t % 2.4) / 0.8);
            ctx.save();
            ctx.translate(x + 95, gy - 18 - (1 - fall * fall) * 60);
            ctx.rotate(fall * 0.6);
            ctx.drawImage(images.pig, -18, -18, 36, 36);
            ctx.restore();
            var rows = [["1 bird", 3], ["2 birds", 2], ["3 birds", 1]];
            for (var r = 0; r < 3; r++) {
                var ry = y + 24 + r * 28;
                text(rows[r][0], x + 236, ry, 13, C.text, "right", 700, "middle");
                for (var s2 = 0; s2 < 3; s2++) drawStar(x + 262 + s2 * 26, ry, 10, s2 < rows[r][1], 1);
            }
            text("Pig still standing", x + 350, y + 38, 12, C.text, "left", 700, "middle");
            text("= 0 stars", x + 350, y + 56, 12, C.text, "left", 600, "middle");
        }
    }

    function draw() {
        applyView(ctx);                                        // sharp drawing (shell.js)
        buttons = [];
        drawBackground();
        drawWalls();
        drawSlingshotBack();
        blocks.forEach(drawBlock);
        drawOnBody(pig, images.pig, 2 * PIG_R, 2 * PIG_R, false);
        if (bird) drawOnBody(bird, images.bird, 2 * BIRD_R, 2 * BIRD_R, false);
        drawSlingshotFront();
        drawWaitingBirds();

        particles.forEach(function (q) {
            ctx.save();
            ctx.globalAlpha = Math.min(1, q.life * 2);
            ctx.translate(q.x, q.y);
            ctx.rotate(q.rot);
            ctx.fillStyle = q.color;
            roundRect(-q.size / 2, -q.size / 2, q.size, q.size, q.size / 4);
            ctx.fill();
            ctx.restore();
        });

        drawAim();
        drawPopups();
        drawHUD();
        drawEndCard();
        drawTutorial();
    }

    // ------------------------------------------------------------------------
    // Loop, start / stop (called by shell.js)
    // ------------------------------------------------------------------------
    function loop() {
        if (!active) { looping = false; return; }
        update();
        draw();
        requestAnimationFrame(loop);
    }

    function start() {
        active = true;
        buildScene();
        openTutorial();                                        // tutorial every time version 2 starts
        if (!looping) { looping = true; requestAnimationFrame(loop); }
    }
    function stop() {
        active = false;
        drag = null;
        canvas.style.cursor = "default";
    }

    var names = Object.keys(imageFiles);
    var loaded = 0;
    names.forEach(function (name) {
        var img = new Image();
        img.onload = function () {
            if (++loaded === names.length) registerVersion(2, { start: start, stop: stop });
        };
        img.src = imageFiles[name];
        images[name] = img;
    });
}
