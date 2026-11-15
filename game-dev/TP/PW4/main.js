
function init() {

    // get canvas
    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext("2d");

    // scale to translate from box2d elements to pixels
    var scale = 20;

    // shortcuts to box2d classes
    var Vec2 = Box2D.Common.Math.b2Vec2;
    var BodyDef = Box2D.Dynamics.b2BodyDef;
    var Body = Box2D.Dynamics.b2Body;
    var FixtureDef = Box2D.Dynamics.b2FixtureDef;
    var World = Box2D.Dynamics.b2World;
    var Polygon = Box2D.Collision.Shapes.b2PolygonShape;
    var Circle = Box2D.Collision.Shapes.b2CircleShape;
    var ContactListener = Box2D.Dynamics.b2ContactListener;

    // 1. Create Physics World (single world for the platform and the dynamic bodies)
    var gravity = new Vec2(0, 10);
    var world = new World(gravity, true);


    // 2. Define Fixtures
    var fixDef = new FixtureDef();
    fixDef.density = 1;
    fixDef.friction = 0.4;
    // restitution : for rebound after collision
    // 0 = no rebound ; 1 = rebound
    fixDef.restitution = 0.2;


    // 3. Create the static platform (from static_main)
    var groundDef = new BodyDef();
    groundDef.type = Body.b2_staticBody;
    // position of the center of the ground, from pixels to meters
    groundDef.position.Set(400 / scale, 280 / scale);
    var groundShape = new Polygon();
    // SetAsBox takes half-width and half-height of the body, in meters
    groundShape.SetAsBox(200 / scale, 20 / scale);
    fixDef.shape = groundShape;
    var groundBody = world.CreateBody(groundDef);
    groundBody.CreateFixture(fixDef);


    // 4. Create a dynamic body: a circle (from dynamic_main, with a b2CircleShape)
    var radius = 30;
    var circleDef = new BodyDef();
    circleDef.type = Body.b2_dynamicBody;
    circleDef.position.Set(400 / scale, 100 / scale);
    var circleShape = new Circle(radius / scale);
    circleShape.SetRadius(radius / scale);
    fixDef.shape = circleShape;
    var circleBody = world.CreateBody(circleDef);
    circleBody.CreateFixture(fixDef);


    // 5. More dynamic bodies: positions and dimensions stored in an array (pixels)
    var extraBodies = [
        { type: "circle", x: 370, y: 20,   r: 20,       fill: "#4caf50", stroke: "#1b5e20" },
        { type: "box",    x: 430, y: -60,  w: 50, h: 50, fill: "#ffd54f", stroke: "#f57f17" },
        { type: "circle", x: 330, y: -140, r: 25,       fill: "#64b5f6", stroke: "#0d47a1" },
        { type: "box",    x: 470, y: -230, w: 40, h: 70, fill: "#ba68c8", stroke: "#4a148c" }
    ];
    // everything that has to be drawn on the canvas, the first one is the main circle
    var shapes = [{ body: circleBody, kind: "circle", r: radius, fill: "#e53935", stroke: "#212121" }];

    // creates a dynamic body (circle or box) from an object of the array and registers it for drawing
    function addBody(b) {
        var def = new BodyDef();
        def.type = Body.b2_dynamicBody;
        def.position.Set(b.x / scale, b.y / scale);
        if (b.type === "circle") {
            fixDef.shape = new Circle(b.r / scale);
        } else {
            var boxShape = new Polygon();
            boxShape.SetAsBox(b.w / 2 / scale, b.h / 2 / scale);
            fixDef.shape = boxShape;
        }
        var body = world.CreateBody(def);
        body.CreateFixture(fixDef);
        shapes.push({ body: body, kind: b.type, r: b.r, w: b.w, h: b.h, fill: b.fill, stroke: b.stroke });
    }

    for (var i = 0; i < extraBodies.length; i++) {
        addBody(extraBodies[i]);
    }

    // click on the canvas: a random circle or box drops from the clicked point
    var colors = [["#4caf50", "#1b5e20"], ["#ffd54f", "#f57f17"], ["#64b5f6", "#0d47a1"],
                  ["#ba68c8", "#4a148c"], ["#ff8a65", "#bf360c"]];
    canvas.addEventListener("click", function (e) {
        var rect = canvas.getBoundingClientRect();
        var c = colors[Math.floor(Math.random() * colors.length)];
        var b = {
            type: Math.random() < 0.5 ? "circle" : "box",
            x: (e.clientX - rect.left) * canvas.width / rect.width,
            y: (e.clientY - rect.top) * canvas.height / rect.height,
            fill: c[0], stroke: c[1]
        };
        if (b.type === "circle") {
            b.r = 15 + Math.random() * 20;
        } else {
            b.w = 30 + Math.random() * 40;
            b.h = 30 + Math.random() * 40;
        }
        addBody(b);
    });


    // 6. Contact listener (from the collision sheet): created after the world, registered once
    // Counts the contacts between ANY two bodies (circle, box or platform), not only the main circle
    var contacts = 0;
    var listener = new ContactListener();

    // Called when two fixtures start touching
    listener.BeginContact = function (contact) {
        contacts++;
    };
    // Called when two fixtures stop touching
    listener.EndContact = function (contact) {
        contacts--;
    };
    world.SetContactListener(listener);


    // 7. Drawing: box2d shapes can't be styled, so draw canvas shapes at the same place and size
    function drawPlatform() {
        var position = groundBody.GetPosition(); // meters
        ctx.fillStyle = "#6d4c41";
        ctx.fillRect(position.x * scale - 200, position.y * scale - 20, 400, 40);
    }

    function drawShape(s) {
        var position = s.body.GetPosition(); // meters, converted back to pixels with scale
        ctx.save();
        ctx.translate(position.x * scale, position.y * scale);
        ctx.rotate(s.body.GetAngle());
        ctx.fillStyle = s.fill;
        ctx.strokeStyle = s.stroke;
        ctx.lineWidth = 3;
        ctx.beginPath();
        if (s.kind === "circle") {
            ctx.arc(0, 0, s.r, 0, Math.PI * 2);
            // a radius line shows the rotation
            ctx.moveTo(0, 0);
            ctx.lineTo(s.r, 0);
        } else {
            ctx.rect(-s.w / 2, -s.h / 2, s.w, s.h);
        }
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    }

    // Message: red when the circle collides, black otherwise
    function drawMessage() {
        ctx.fillStyle = contacts > 0 ? "red" : "black";
        ctx.font = "bold 24px Arial";
        ctx.fillText(contacts > 0 ? "Collision!" : "No collision", 20, 40);
    }


    // 8. Add gameloop
    function gameLoop() {
        // Update the physics simulation
        world.Step(
            1 / 60,  // Time step
            10,      // Velocity iterations
            10       // Position iterations
        );
        // Remove the bodies that fell out of the scene (after Step, never inside a contact callback)
        for (var k = shapes.length - 1; k >= 0; k--) {
            if (shapes[k].body.GetPosition().y * scale > canvas.height + 200) {
                world.DestroyBody(shapes[k].body);
                shapes.splice(k, 1);
            }
        }
        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // Draw the bodies
        drawPlatform();
        for (var k = 0; k < shapes.length; k++) drawShape(shapes[k]);
        drawMessage();
        // Prepare the next frame
        requestAnimationFrame(gameLoop);
    }

    gameLoop();

}
