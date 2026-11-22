// =====================================================================
// AI DISCLOSURE (required by the midterm sheet)
// Tool   : Claude (Anthropic)
// Method : the game was generated in 7 successive prompts (one per
//          requirement of the midterm sheet). The exact text of each prompt
//          is quoted, word for word, in a "[AI] Prompt N" comment above the
//          code it produced:
//            Prompt 1 : physics world   -> section 1 (world, ground, loop)
//            Prompt 2 : dynamic objects -> section 2 (bird, pig)
//            Prompt 3 : obstacles       -> section 3 (+ createBox/createCircle)
//            Prompt 4 : sprites         -> images + drawBodies()
//            Prompt 5 : launch          -> section 5 (mouse slingshot)
//            Prompt 6 : collisions      -> section 6 (ContactListener, message)
//            Prompt 7 : walls           -> section 7 (+ final review)
// =====================================================================

function init() {
  // get canvas
  var canvas = document.getElementById("canvas");
  var ctx = canvas.getContext("2d");

  // scale to translate from box2d elements (meters) to pixels
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

  // [AI] Prompt 4 (sprites), used here for the image loading, exact text:
  // "Step 4/7. Replace the debug drawing with sprites. Load red.png,
  // target.png, wood_bar.png, wood_box.png and rock_ball.png with Image
  // objects. Store the image and its pixel size in each body's userData
  // (SetUserData). Write drawBodies(): loop on world.GetBodyList() with
  // GetNext(), and for each body use ctx.save(), ctx.translate(pos.x *
  // scale, pos.y * scale), ctx.rotate(body.GetAngle()), ctx.drawImage
  // centered at -w/2, -h/2, then ctx.restore(). Draw the ground and later
  // the walls as colored fillRect shapes. Clear the canvas every frame,
  // call world.ClearForces() after Step, and explain why the sprites
  // follow both position and rotation."
  // (the rest of this prompt is used in drawBodies() and in the game loop)
  function loadImage(src) {
    var img = new Image();
    img.src = src;
    return img;
  }
  var redImg = loadImage("sprites/red.png");
  var pigImg = loadImage("sprites/target.png");
  var barImg = loadImage("materials/wood_bar.png");
  var boxImg = loadImage("materials/wood_box.png");
  var ballImg = loadImage("materials/rock_ball.png");

  // ---------------------------------------------------------------
  // 1. Create Physics World
  // [AI] Prompt 1 (physics world), exact text:
  // "Angry Birds exercise, step 1/7. Work in index.html + main.js, same
  // style as Chapter3-Demo: an init() function, var shortcuts to the
  // Box2D classes (b2Vec2, b2BodyDef, b2Body, b2FixtureDef, b2World,
  // b2PolygonShape), a scale constant of 20 px per meter, and a canvas of
  // 800x560. Create the b2World with gravity Vec2(0, 10) and doSleep =
  // true. Add a b2_staticBody ground (SetAsBox takes half-width and
  // half-height) so its top edge is at y = 520 px, and give the fixture
  // density, friction and restitution. Start the game loop with
  // requestAnimationFrame calling world.Step(1/60, 10, 10), and display
  // the bodies with b2DebugDraw for now. Comment every step."
  // (b2DebugDraw was replaced by sprites in Prompt 4)
  // ---------------------------------------------------------------
  // gravity, it's a vector showing horizontal and vertical forces
  var gravity = new Vec2(0, 10);
  // create world (true = bodies that are at rest are allowed to sleep)
  var world = new World(gravity, true);

  // [AI] Prompt 3 (obstacles), used here for the two helpers, exact text:
  // "Step 3/7. Add 6 dynamic obstacles as a tower. Use two vertical posts
  // (box shapes: a 100x12 px bar rotated by bodyDef.angle = Math.PI/2)
  // and one 120x12 px horizontal plank resting on top of them. Also add
  // two 50x50 px boxes stacked at x = 720 px and one circular rock ball
  // of radius 21 px at x = 450 px. Compute every y position so that the
  // bodies rest exactly on the ground (top at y = 520) or on each other
  // without overlap. Refactor the repeated body creation into two
  // helpers, createBox and createCircle, that take pixel values, convert
  // them to meters, and attach a userData object with a name to each
  // body."
  // createBox: body with a box shape. Values are given in pixels and
  // converted to meters. "data" is stored in the body (SetUserData).
  function createBox(type, x, y, halfW, halfH, angle, density, data) {
    var fixDef = new FixtureDef();
    fixDef.density = density;
    fixDef.friction = 0.6;
    // restitution : for rebound after collision
    fixDef.restitution = 0.1;
    var bodyDef = new BodyDef();
    bodyDef.type = type;
    bodyDef.position.Set(x / scale, y / scale);
    bodyDef.angle = angle;
    // SetAsBox takes half-width and half-height, in meters
    var shape = new Polygon();
    shape.SetAsBox(halfW / scale, halfH / scale);
    fixDef.shape = shape;
    var body = world.CreateBody(bodyDef);
    body.CreateFixture(fixDef);
    body.SetUserData(data);
    return body;
  }

  // createCircle (Prompt 3 helper): same thing but with a circle shape
  function createCircle(type, x, y, radius, density, restitution, data) {
    var fixDef = new FixtureDef();
    fixDef.density = density;
    fixDef.friction = 0.6;
    fixDef.restitution = restitution;
    var bodyDef = new BodyDef();
    bodyDef.type = type;
    bodyDef.position.Set(x / scale, y / scale);
    fixDef.shape = new Circle(radius / scale);
    var body = world.CreateBody(bodyDef);
    body.CreateFixture(fixDef);
    body.SetUserData(data);
    return body;
  }

  // static ground: center (400, 540), 800 x 40 pixels -> its top is at y = 520
  createBox(Body.b2_staticBody, 400, 540, 400, 20, 0, 1, {
    name: "ground",
    color: "green",
    w: 800,
    h: 40,
  });

  // ---------------------------------------------------------------
  // 7. Add walls (static bodies on the left and right sides)
  // [AI] Prompt 7 (walls), exact text:
  // "Step 7/7. Add two static walls, 20x560 px, centered on x = 0 and
  // x = 800, so the bodies cannot leave the playable area. Draw them as
  // colored rectangles through the same userData-based drawing code.
  // Then review the whole main.js: add a comment above every section,
  // check that every pixel-to-meter conversion is consistent, and list
  // what would change to add a ceiling."
  // ---------------------------------------------------------------
  // 20 x 560 pixels each, centered on the left and right edges of the canvas
  createBox(Body.b2_staticBody, 0, 280, 10, 280, 0, 1, {
    name: "wall",
    color: "#8b5a2b",
    w: 20,
    h: 560,
  });
  createBox(Body.b2_staticBody, 800, 280, 10, 280, 0, 1, {
    name: "wall",
    color: "#8b5a2b",
    w: 20,
    h: 560,
  });

  // ---------------------------------------------------------------
  // 2. Add dynamic objects
  // [AI] Prompt 2 (dynamic objects), exact text:
  // "Step 2/7. Add the two dynamic bodies (b2_dynamicBody) using the same
  // BodyDef/FixtureDef/shape pattern. The player (red bird) is a
  // b2CircleShape of radius 20 px resting on the ground at x = 150 px,
  // with density 2 and restitution 0.3. The target (green pig) is a
  // b2CircleShape of radius 24 px placed on top of a future tower at
  // x = 600 px, y = 384 px. Explain why a circle is the right collision
  // shape for both. Convert every pixel value to meters with the scale
  // constant. Keep the code in the numbered-section comment style."
  // ---------------------------------------------------------------
  // 2.1 the player (red bird): circle of radius 20 px, resting on the ground
  // (ground top = 520, so center y = 520 - 20 = 500). Heavy and a bit bouncy.
  var bird = createCircle(Body.b2_dynamicBody, 150, 500, 20, 2, 0.3, {
    name: "bird",
    img: redImg,
    w: 40,
    h: 40,
  });

  // 2.2 the target (green pig): circle of radius 24 px, on top of the tower
  // (plank top = 408, so center y = 408 - 24 = 384)
  var pig = createCircle(Body.b2_dynamicBody, 600, 384, 24, 1, 0.1, {
    name: "pig",
    img: pigImg,
    w: 48,
    h: 48,
  });

  // ---------------------------------------------------------------
  // 3. Add obstacles (6 dynamic bodies: 3 bars, 2 boxes, 1 ball)
  // [AI] Prompt 3 (obstacles): same prompt as quoted above the helpers
  // createBox / createCircle (2 posts + plank, 2 stacked boxes, 1 rock).
  // ---------------------------------------------------------------
  // wood bar: 100 x 12 px sprite, so half sizes are 50 x 6
  // two vertical posts: the same bar rotated by PI/2
  createBox(Body.b2_dynamicBody, 560, 470, 50, 6, Math.PI / 2, 1, {
    name: "post",
    img: barImg,
    w: 100,
    h: 12,
  });
  createBox(Body.b2_dynamicBody, 640, 470, 50, 6, Math.PI / 2, 1, {
    name: "post",
    img: barImg,
    w: 100,
    h: 12,
  });
  // horizontal plank on top of the posts (120 x 12 px)
  createBox(Body.b2_dynamicBody, 600, 414, 60, 6, 0, 1, {
    name: "plank",
    img: barImg,
    w: 120,
    h: 12,
  });
  // two wooden boxes stacked on the right (50 x 50 px)
  createBox(Body.b2_dynamicBody, 720, 495, 25, 25, 0, 1, {
    name: "box",
    img: boxImg,
    w: 50,
    h: 50,
  });
  createBox(Body.b2_dynamicBody, 720, 445, 25, 25, 0, 1, {
    name: "box",
    img: boxImg,
    w: 50,
    h: 50,
  });
  // a heavy rock ball (circle, radius 21 px) in front of the tower
  createCircle(Body.b2_dynamicBody, 450, 499, 21, 3, 0.2, {
    name: "ball",
    img: ballImg,
    w: 42,
    h: 42,
  });

  // ---------------------------------------------------------------
  // 6. Detect collisions: pig <-> ground
  // [AI] Prompt 6 (collisions), exact text:
  // "Step 6/7. Detect when the target hits the ground. Create a
  // b2ContactListener, override BeginContact, and read the userData of
  // both bodies through contact.GetFixtureA().GetBody() and
  // GetFixtureB().GetBody(). Because A and B are in arbitrary order, test
  // both combinations of "pig" and "ground". Set a pigOnGround flag,
  // register the listener with world.SetContactListener, and draw the
  // message on the canvas every frame: "No targets on the ground yet" in
  // black before, and "Bravo !" in red after. Explain why BeginContact is
  // better than checking positions every frame."
  // (the message drawing part of this prompt is in drawMessage() below)
  // ---------------------------------------------------------------
  var pigOnGround = false;
  var listener = new ContactListener();
  // called by box2d once, when two fixtures start touching
  listener.BeginContact = function (contact) {
    // the user data of the two bodies involved in the contact
    var a = contact.GetFixtureA().GetBody().GetUserData();
    var b = contact.GetFixtureB().GetBody().GetUserData();
    if (a && b) {
      if (
        (a.name === "pig" && b.name === "ground") ||
        (a.name === "ground" && b.name === "pig")
      ) {
        pigOnGround = true;
      }
    }
  };
  world.SetContactListener(listener);

  // ---------------------------------------------------------------
  // 5. Launch the player body by clicking and dragging the mouse
  // [AI] Prompt 5 (launch), exact text:
  // "Step 5/7. Launch the bird with mouse drag, like a slingshot. On
  // mousedown, accept the click only if it is within 50 px of the bird
  // and the bird is not already launched. On mousemove, compute the pull
  // vector (mouse minus bird position, in canvas coordinates through
  // getBoundingClientRect) limited to 150 px. Draw a line from the bird
  // to the pull point while dragging. On mouseup, call bird.SetAwake(true)
  // and bird.SetLinearVelocity with the opposite of the pull vector,
  // converted to meters and multiplied by a power of 3. Register
  // mousemove and mouseup on document so releasing outside the canvas
  // still launches, and allow only one launch."
  // (the aim line of this prompt is drawn by drawAim() below)
  // ---------------------------------------------------------------
  var power = 3; // meters/second given per meter of drag
  var maxDrag = 150; // max drag length in pixels
  var dragging = false; // true between mousedown and mouseup
  var launched = false; // the bird can only be launched once
  var pull = { x: 0, y: 0 }; // drag vector (bird -> mouse), in pixels

  // mouse position in canvas pixels
  function getMouse(e) {
    var rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  // update "pull" from the mouse, limited to maxDrag pixels
  function updatePull(e) {
    var m = getMouse(e);
    var p = bird.GetPosition();
    var dx = m.x - p.x * scale;
    var dy = m.y - p.y * scale;
    var len = Math.sqrt(dx * dx + dy * dy);
    if (len > maxDrag) {
      dx = (dx * maxDrag) / len;
      dy = (dy * maxDrag) / len;
    }
    pull.x = dx;
    pull.y = dy;
  }

  canvas.addEventListener("mousedown", function (e) {
    // start the drag only when the click is on (or near) the bird
    var m = getMouse(e);
    var p = bird.GetPosition();
    var dx = m.x - p.x * scale;
    var dy = m.y - p.y * scale;
    if (!launched && Math.sqrt(dx * dx + dy * dy) < 50) {
      dragging = true;
      updatePull(e);
    }
  });

  document.addEventListener("mousemove", function (e) {
    if (dragging) {
      updatePull(e);
    }
  });

  document.addEventListener("mouseup", function () {
    if (dragging) {
      dragging = false;
      launched = true;
      // the bird goes in the opposite direction of the drag (slingshot):
      // speed = -pull converted to meters, times power
      bird.SetAwake(true);
      bird.SetLinearVelocity(
        new Vec2((-pull.x / scale) * power, (-pull.y / scale) * power),
      );
    }
  });

  // ---------------------------------------------------------------
  // 4. Draw the sprites (follow the position and rotation of the bodies)
  // [AI] Prompt 4 (sprites): drawBodies() implements the second half of
  // the prompt quoted above the image loading (GetBodyList/GetNext loop,
  // save/translate/rotate/drawImage/restore, fillRect for ground + walls).
  // ---------------------------------------------------------------
  function drawBodies() {
    // go through all the bodies of the world
    for (var b = world.GetBodyList(); b; b = b.GetNext()) {
      var data = b.GetUserData();
      if (!data) {
        continue;
      }
      var pos = b.GetPosition();
      ctx.save();
      // move the origin to the center of the body (meters -> pixels)
      ctx.translate(pos.x * scale, pos.y * scale);
      // rotate the canvas by the angle of the body
      ctx.rotate(b.GetAngle());
      if (data.img) {
        // sprite centered on the body
        ctx.drawImage(data.img, -data.w / 2, -data.h / 2, data.w, data.h);
      } else {
        // canvas form for ground and walls
        ctx.fillStyle = data.color;
        ctx.fillRect(-data.w / 2, -data.h / 2, data.w, data.h);
      }
      ctx.restore();
    }
  }

  // [AI] Prompt 5: "Draw a line from the bird to the pull point while
  // dragging." (aim line)
  function drawAim() {
    if (!dragging) {
      return;
    }
    var p = bird.GetPosition();
    ctx.beginPath();
    ctx.moveTo(p.x * scale, p.y * scale);
    ctx.lineTo(p.x * scale + pull.x, p.y * scale + pull.y);
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  // [AI] Prompt 6: "draw the message on the canvas every frame: "No
  // targets on the ground yet" in black before, and "Bravo !" in red after."
  function drawMessage() {
    ctx.font = "16px Arial";
    if (pigOnGround) {
      ctx.fillStyle = "red";
      ctx.fillText("Bravo !", 20, 30);
    } else {
      ctx.fillStyle = "black";
      ctx.fillText("No targets on the ground yet", 20, 30);
    }
  }

  // ---------------------------------------------------------------
  // Game loop
  // [AI] Prompt 1: "Start the game loop with requestAnimationFrame calling
  // world.Step(1/60, 10, 10)". Prompt 4: "Clear the canvas every frame,
  // call world.ClearForces() after Step".
  // ---------------------------------------------------------------
  function gameLoop() {
    // Update the physics simulation
    world.Step(
      1 / 60, // Time step
      10, // Velocity iterations
      10, // Position iterations
    );
    world.ClearForces();
    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Draw the bodies, the aim line and the message
    drawBodies();
    drawAim();
    drawMessage();
    // Prepare the next frame
    requestAnimationFrame(gameLoop);
  }

  gameLoop();
}
