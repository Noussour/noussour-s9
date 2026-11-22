// ============================================================================
// Angry Birds-style game with HTML5 Canvas and Box2DWeb
// VERSION 1: the answer to the midterm subject (key 1)
//
// AI USED: this whole file was written with Claude Code (AI assistant).
// Prompt used: "read the newly added test for game dev, i want you to go on and
//               solve it entirely for me"
// Then modified with the prompt: "improve on it so when clicking 2 an entirely new
//   version of the game is shown [...] and also make it that when hitting f the
//   canvas is in full screen" (start/stop so keys 1 and 2 can switch versions,
//   mouse position that also works in fullscreen)
// And: "make it [...] not that pixelated" (logical 800 x 450 size, applyView in draw)
// ============================================================================

function init() {

    var active = false;   // true while version 1 is the one on screen

    // ---------- Canvas ----------
    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext("2d");
    var W = VIEW_W;     // logical size (800 x 450), see shell.js
    var H = VIEW_H;

    // scale to translate from box2d meters to pixels (1 meter = 30 pixels)
    var scale = 30;

    // shortcuts to box2d classes
    var Vec2 = Box2D.Common.Math.b2Vec2;
    var BodyDef = Box2D.Dynamics.b2BodyDef;
    var Body = Box2D.Dynamics.b2Body;
    var FixtureDef = Box2D.Dynamics.b2FixtureDef;
    var World = Box2D.Dynamics.b2World;
    var Polygon = Box2D.Collision.Shapes.b2PolygonShape;
    var Circle = Box2D.Collision.Shapes.b2CircleShape;
    var ContactListener = Box2D.Dynamics.b2ContactListener;

    // y (in pixels) of the top of the ground
    var GROUND_TOP = 410;

    // ---------- Images (the provided materials) ----------
    var imageFiles = {
        bird:    "sprites/red.png",
        pig:     "sprites/target.png",
        woodBar: "materials/wood_bar.png",
        woodBox: "materials/wood_box.png",
        iceBox:  "materials/ice_box.png",
        rockBox: "materials/rock_box.png"
    };
    var images = {};

    // ---------- Game state (rebuilt by buildScene) ----------
    var world;
    var items;            // everything drawn with an image: { body, img, dw, dh, vertical }
    var bird, birdRadius; // the player
    var targetOnGround;   // true when the pig has touched the ground
    var drag = null;      // slingshot drag in progress: { ax, ay, x, y } in pixels
    var ready;            // true while the bird waits on the slingshot (before the launch)

    // where the bird waits on the slingshot (pixels)
    var SLING_X = 140;
    var SLING_Y = 310;

    // launch: speed (m/s) per meter of pull, and maximum pull in pixels
    var PULL_TO_SPEED = 5;
    var MAX_PULL = 110;

    // ------------------------------------------------------------------------
    // Helpers to create bodies
    // ------------------------------------------------------------------------

    // a fixture definition with its own material
    function material(density, friction, restitution) {
        var f = new FixtureDef();
        f.density = density;
        f.friction = friction;
        f.restitution = restitution;
        return f;
    }

    // static box (ground, walls): x, y = center in pixels, w, h = size in pixels
    function addStaticBox(x, y, w, h, name) {
        var def = new BodyDef();
        def.type = Body.b2_staticBody;
        def.position.Set(x / scale, y / scale);
        var shape = new Polygon();
        // SetAsBox takes the half-width and half-height
        shape.SetAsBox(w / 2 / scale, h / 2 / scale);
        var fix = material(1, 0.6, 0.1);
        fix.shape = shape;
        var body = world.CreateBody(def);
        body.CreateFixture(fix);
        body.SetUserData(name);
        return body;
    }

    // dynamic box with an image (obstacles). vertical = the image is drawn turned by 90 degrees
    function addObstacle(x, y, w, h, img, vertical, density) {
        var def = new BodyDef();
        def.type = Body.b2_dynamicBody;
        def.position.Set(x / scale, y / scale);
        var shape = new Polygon();
        shape.SetAsBox(w / 2 / scale, h / 2 / scale);
        var fix = material(density, 0.6, 0.1);
        fix.shape = shape;
        var body = world.CreateBody(def);
        body.CreateFixture(fix);
        body.SetUserData("obstacle");
        items.push({
            body: body, img: img, vertical: vertical,
            dw: vertical ? h : w,    // size of the image once turned back to horizontal
            dh: vertical ? w : h
        });
    }

    // dynamic circle with an image (bird and pig)
    function addBall(x, y, r, img, density, restitution, name) {
        var def = new BodyDef();
        def.type = Body.b2_dynamicBody;
        def.position.Set(x / scale, y / scale);
        var fix = material(density, 0.6, restitution);
        fix.shape = new Circle(r / scale);
        var body = world.CreateBody(def);
        body.CreateFixture(fix);
        body.SetUserData(name);
        items.push({ body: body, img: img, vertical: false, dw: 2 * r, dh: 2 * r });
        return body;
    }

    // ------------------------------------------------------------------------
    // 1. Physics world, 2. dynamic objects, 3. obstacles, 7. walls
    // ------------------------------------------------------------------------
    function buildScene() {
        // 1. Create the world: gravity pointing down (y axis goes down on a canvas)
        world = new World(new Vec2(0, 10), true);
        items = [];
        targetOnGround = false;
        drag = null;
        ready = true;

        // 1. Static ground platform
        addStaticBox(W / 2, GROUND_TOP + 20, W, 40, "ground");

        // 7. Walls on both sides (taller than the scene so nothing can leave)
        addStaticBox(0, 0, 20, 2 * H, "wall");
        addStaticBox(W, 0, 20, 2 * H, "wall");

        // 3. Obstacles: a tower of two posts and a plank, a box inside it,
        //    and two boxes stacked next to it (6 obstacles, all dynamic boxes)
        addObstacle(520, 360, 14, 100, images.woodBar, true, 0.6);    // left post
        addObstacle(600, 360, 14, 100, images.woodBar, true, 0.6);    // right post
        addObstacle(560, 303, 130, 14, images.woodBar, false, 0.6);   // plank on top
        addObstacle(560, 387, 46, 46, images.woodBox, false, 0.6);    // box inside the tower
        addObstacle(690, 386, 48, 48, images.iceBox, false, 0.5);     // ice box
        addObstacle(690, 338, 48, 48, images.rockBox, false, 1.5);    // rock box on the ice box

        // 2. Dynamic bodies: the target (green pig) and the player (red bird).
        //    Both are round, so the collision shape is a circle.
        addBall(560, 274, 22, images.pig, 1, 0.2, "target");
        birdRadius = 20;
        bird = addBall(SLING_X, SLING_Y, birdRadius, images.bird, 2, 0.3, "bird");

        // 6. Collision detection: the contact listener is created after the world
        var listener = new ContactListener();
        listener.BeginContact = function (contact) {
            var a = contact.GetFixtureA().GetBody().GetUserData();
            var b = contact.GetFixtureB().GetBody().GetUserData();
            // the target touches the ground
            if ((a === "target" && b === "ground") || (a === "ground" && b === "target")) {
                targetOnGround = true;
            }
        };
        world.SetContactListener(listener);
    }

    // ------------------------------------------------------------------------
    // 5. Launch the bird by clicking and dragging the mouse
    // ------------------------------------------------------------------------

    // mouse position in canvas pixels (canvasPoint is in shell.js, it also works in fullscreen)
    function mousePos(e) {
        return canvasPoint(e);
    }

    // mouse down on the bird: start pulling it
    canvas.addEventListener("mousedown", function (e) {
        if (!active) return;
        var m = mousePos(e);
        var p = bird.GetPosition();
        var dx = m.x - p.x * scale, dy = m.y - p.y * scale;
        if (Math.sqrt(dx * dx + dy * dy) <= birdRadius + 10) {
            // the pull starts from where the bird is (the slingshot, or where it landed)
            drag = { ax: p.x * scale, ay: p.y * scale, x: p.x * scale, y: p.y * scale };
        }
    });

    // mouse move: the bird follows the mouse, but not too far from where it started
    document.addEventListener("mousemove", function (e) {
        if (!active || !drag) return;
        var m = mousePos(e);
        var dx = m.x - drag.ax, dy = m.y - drag.ay;
        var len = Math.sqrt(dx * dx + dy * dy);
        if (len > MAX_PULL) {
            dx = dx * MAX_PULL / len;
            dy = dy * MAX_PULL / len;
        }
        drag.x = drag.ax + dx;
        // stay above the ground
        drag.y = Math.min(drag.ay + dy, GROUND_TOP - birdRadius);
    });

    // mouse up: the bird is launched with a speed proportional to the pull,
    // in the direction opposite to the pull
    document.addEventListener("mouseup", function () {
        if (!active || !drag) return;
        var vx = (drag.ax - drag.x) / scale * PULL_TO_SPEED;
        var vy = (drag.ay - drag.y) / scale * PULL_TO_SPEED;
        bird.SetLinearVelocity(new Vec2(vx, vy));
        drag = null;
        ready = false;
    });

    // R restarts the scene
    document.addEventListener("keydown", function (e) {
        if (active && (e.key === "r" || e.key === "R")) buildScene();
    });

    // ------------------------------------------------------------------------
    // 4. Drawing
    // ------------------------------------------------------------------------

    // draw an image on its body: the sprite follows the position and the rotation
    function drawItem(it) {
        var p = it.body.GetPosition();            // meters -> pixels with scale
        ctx.save();
        ctx.translate(p.x * scale, p.y * scale);
        ctx.rotate(it.body.GetAngle());
        if (it.vertical) ctx.rotate(Math.PI / 2); // bars are drawn horizontally in the image file
        ctx.drawImage(it.img, -it.dw / 2, -it.dh / 2, it.dw, it.dh);
        ctx.restore();
    }

    function draw() {
        applyView(ctx);      // sharp drawing at the real screen resolution (shell.js)
        ctx.clearRect(0, 0, W, H);

        // ground (static body)
        ctx.fillStyle = "green";
        ctx.fillRect(0, GROUND_TOP, W, H - GROUND_TOP);
        // walls (static bodies, half of their width is visible)
        ctx.fillStyle = "#666";
        ctx.fillRect(0, 0, 10, H);
        ctx.fillRect(W - 10, 0, 10, H);
        // slingshot (only a drawing, not a physics body)
        ctx.fillStyle = "#6d4c41";
        ctx.fillRect(SLING_X - 6, SLING_Y + birdRadius - 5, 12, GROUND_TOP - SLING_Y - birdRadius + 5);

        // obstacles, target and player
        for (var i = 0; i < items.length; i++) drawItem(items[i]);

        // slingshot: rubber band while dragging
        if (drag) {
            ctx.strokeStyle = "#5d4037";
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(drag.ax, drag.ay);
            ctx.lineTo(drag.x, drag.y);
            ctx.stroke();
        }

        // 6. Message
        ctx.font = "14px Arial";
        if (targetOnGround) {
            ctx.fillStyle = "red";
            ctx.fillText("Bravo !", 15, 25);
        } else {
            ctx.fillStyle = "black";
            ctx.fillText("No targets on the ground yet", 15, 25);
        }
    }

    // ------------------------------------------------------------------------
    // Game loop
    // ------------------------------------------------------------------------
    function gameLoop() {
        // stop the loop when another version is shown
        if (!active) { looping = false; return; }
        // before the launch the bird stays on the slingshot, and while dragging
        // it is held at the pulled position
        if (drag || ready) {
            var hx = drag ? drag.x : SLING_X;
            var hy = drag ? drag.y : SLING_Y;
            bird.SetPosition(new Vec2(hx / scale, hy / scale));
            bird.SetLinearVelocity(new Vec2(0, 0));
            bird.SetAngularVelocity(0);
            bird.SetAwake(true);
        }
        world.Step(1 / 60, 10, 10);
        world.ClearForces();
        draw();
        requestAnimationFrame(gameLoop);
    }

    // start / stop, used by shell.js to switch between versions 1 and 2
    var looping = false;
    function start() {
        active = true;
        buildScene();
        if (!looping) { looping = true; requestAnimationFrame(gameLoop); }
    }
    function stop() {
        active = false;
    }

    // load all the images, then register this version (shell.js starts it)
    var names = Object.keys(imageFiles);
    var loaded = 0;
    names.forEach(function (name) {
        var img = new Image();
        img.onload = function () {
            loaded++;
            if (loaded === names.length) {
                registerVersion(1, { start: start, stop: stop });
            }
        };
        img.src = imageFiles[name];
        images[name] = img;
    });
}
