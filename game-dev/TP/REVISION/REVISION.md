# Game Dev exam revision: HTML canvas games

Covers everything from the TPs (TP0 basics, PW1 sprites, PW2 tiles and scrolling, PW3 isometric, PW4 Box2DWeb) plus the course theory (chapters 1 to 3).

**How to use this kit**

1. Read sections 1 to 8 once, with the matching file from this folder open (`01-...html` to `08-...html`). Every file runs by double-click and is commented line by line.
2. Close the files. Re-write each template from a blank page, from memory. Do it until you can write the skeleton (section 1) in under 3 minutes.
3. Do the drills (section 10), then the theory questions (section 9).

| File | Topic | TP |
|---|---|---|
| `01-canvas-basics.html` | shapes, colours, text, save/restore, images | TP0 |
| `02-game-loop-keyboard.html` | game loop, keyboard, delta time | TP0 / PW1 |
| `03-sprite-animation.html` | spritesheet, frame timing, directions | PW1 |
| `04-tilemap-scroll.html` | tilemap, camera, scrolling, tile collisions | PW2 |
| `05-isometric.html` | isometric projection and its inverse | PW3 |
| `06-box2d.html` | Box2DWeb world, bodies, contacts, click to spawn | PW4 |
| `07-collisions.html` | AABB, circle, circle-rect, point-rect | Chapter 3 |
| `08-mini-game.html` | a whole small game (coins, enemies, lives, game over) | everything |

Your real TP solutions are also good reference: `../TP3/` (isometric map, sprite, combined scene) and `../PW4/` (Box2D).

---

## 1. The skeleton to know by heart

If you remember only one thing, remember this. Every canvas game is this.

```html
<canvas id="c" width="600" height="400"></canvas>
<script>
var canvas = document.getElementById('c');
var ctx = canvas.getContext('2d');

var player = { x: 100, y: 100, w: 32, h: 32, speed: 200 };   // STATE
var keys = {};                                               // INPUT
document.addEventListener("keydown", function (e) { keys[e.key] = true; });
document.addEventListener("keyup",   function (e) { keys[e.key] = false; });

function update(dt) {                                        // UPDATE (dt in seconds)
    if (keys["ArrowRight"]) player.x += player.speed * dt;
    if (keys["ArrowLeft"])  player.x -= player.speed * dt;
}
function draw() {                                            // DRAW
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillRect(player.x, player.y, player.w, player.h);
}
var last = 0;
function loop(now) {                                         // LOOP
    var dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    update(dt); draw();
    requestAnimationFrame(loop);
}
requestAnimationFrame(function (t) { last = t; loop(t); });
</script>
```

The course version (TP0) is simply `function gameLoop(){ update(); draw(); requestAnimationFrame(gameLoop); }` and calling `gameLoop()` once. If the exam gives you that form, use it. The `dt` version is a bonus.

**Order inside a frame: read input, update state, clear, draw, schedule the next frame.**

---

## 2. Canvas API cheat sheet (TP0)

| I want to... | Code |
|---|---|
| get the context | `var ctx = document.getElementById('id').getContext('2d');` |
| filled rectangle | `ctx.fillStyle = "red"; ctx.fillRect(x, y, w, h);` |
| rectangle border | `ctx.strokeStyle = "blue"; ctx.lineWidth = 3; ctx.strokeRect(x, y, w, h);` |
| circle | `ctx.beginPath(); ctx.arc(x, y, r, 0, 2*Math.PI); ctx.fill();` (or `ctx.stroke()`) |
| line | `ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();` |
| colour | `"red"`, `"#ff0000"`, `"rgb(255,0,0)"`, `"rgba(255,0,0,0.5)"` (alpha 0 transparent to 1 opaque) |
| text | `ctx.font = "20px Arial"; ctx.textAlign = "center"; ctx.fillText("Hi", x, y);` |
| erase everything | `ctx.clearRect(0, 0, canvas.width, canvas.height);` |
| whole image | `ctx.drawImage(img, x, y);` |
| part of an image | `ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);` |
| load an image | `var img = new Image(); img.src = "a.png"; img.onload = function(){ ... };` |
| protect settings | `ctx.save(); ... ctx.restore();` |
| move origin / rotate / scale | `ctx.translate(x,y); ctx.rotate(angleRadians); ctx.scale(sx,sy);` |

Details that cost points:

- `ctx.clear()` does not exist for the 2D context. Use `clearRect`.
- `fillStyle` and `strokeStyle` stay set until you change them. That is why `save/restore` exists.
- `save/restore` stores the **settings** (colours, transforms), not the pixels.
- `rotate` takes **radians**: `degrees * Math.PI / 180`. It rotates around the current origin, so to rotate an object around its centre: `translate(cx, cy)`, `rotate(a)`, draw centred on `(0,0)`.
- `drawImage` before `onload` draws nothing (and no error). Wait for the load, or start the loop from `onload`.
- Flip a sprite horizontally: `ctx.save(); ctx.translate(x + w, y); ctx.scale(-1, 1); ctx.drawImage(img, 0, 0); ctx.restore();`
- The canvas `width`/`height` **attributes** set the drawing size. Setting them with CSS only stretches the picture.
- Canvas y axis points **down**. (0,0) is the top-left corner.

**Mouse position on the canvas** (used in click-to-spawn):

```js
canvas.addEventListener("click", function (e) {
    var rect = canvas.getBoundingClientRect();
    var x = e.clientX - rect.left, y = e.clientY - rect.top;
});
```

`requestAnimationFrame(cb)` runs `cb` before the next repaint (about 60 times per second, paused in hidden tabs). `setInterval(cb, delay)` runs it every `delay` ms regardless. Both are accepted by the TP.

---

## 3. Keyboard and movement (TP0, PW2)

Two patterns:

1. **Key state object** (smooth, several keys at once): `keys[e.key] = true/false` on keydown/keyup, read it in `update`. Used in `02` and `08`.
2. **Step on keydown** (grid games, isometric TP3): move one cell per key press inside the `keydown` handler, then redraw. Used in `05` and your `isometric_sprite.html`.

`event.key` gives `"ArrowLeft"`, `"ArrowRight"`, `"ArrowUp"`, `"ArrowDown"`, `" "` (space), `"a"`. The old `event.keyCode` gives 37 (left), 38 (up), 39 (right), 40 (down); your TP3 files use it.

Frame-independent speed: `x += speed * dt` where `dt` is in seconds and `speed` in pixels per second. Without `dt`, the game is faster on a 144 Hz screen.

Keep inside the canvas (clamp): `x = Math.max(0, Math.min(x, canvas.width - w));`

---

## 4. Sprites and animation (PW1)

**Definitions.** Sprite: image of an object independent of the background grid. Frame: one image of the animation. Spritesheet: all frames in one PNG (transparent background).

**Formulas** (frame size `FW x FH`, `column` = frame index, `row` = direction/sequence):

```
sourceX = column * FW
sourceY = row * FH
column  = (column + 1) % NB_FRAMES          // loops 0,1,2,3,0,...
frames per row = sheetWidth / FW            // 320 / 32 = 10
```

```js
ctx.drawImage(sheet, column * FW, row * FH, FW, FH,   // source rectangle in the sheet
                     x, y, FW, FH);                   // destination on the canvas
```

**Timing.** Do not change frame on every loop call (60 fps would be a blur). Accumulate time:

```js
frameTimer += dtMs;
if (frameTimer >= 100) { frameTimer -= 100; frame = (frame + 1) % NB_FRAMES; }   // 10 frames per second
```

Or in step games (TP3), change the frame when the key is pressed.

**The TP1 trap (asked in the sheet).** A `for` loop that draws all frames runs in a fraction of a millisecond: without `clearRect` the frames pile up on top of each other; with `clearRect` only the last frame remains. An animation needs the drawing to be **spread over time**, so a loop that runs continuously: `requestAnimationFrame` or `setInterval`.

**Direction rows (your `Character0_Run.png`).** Row 0 = down-left, row 1 = up-left, row 2 = down-right, row 3 = up-right, 4 frames per row. Check the sheet to see which row is which direction. This is the first thing to verify in an exam.

Piskel: draw frames, export as PNG spritesheet choosing columns and rows. The resolution is the frame size.

---

## 5. Tiles, tilemap, scrolling (PW2)

**Vocabulary.** Tile: small reusable image. Tileset: one image holding all tiles. Tilemap: grid of tile ids. Visual grid: what is drawn. Logical grid: what the tile *means* (solid, danger, passable). Do not use the picture alone as the collision rule.

**Tiled export.** CSV with one number per cell. In Tiled, the id in the file is `tile index in the tileset + 1`, and `0` means empty. So to find the piece in the tileset: `index = id - 1`.

```js
var cols = tilesetWidth / TILE;                  // tiles per row in the tileset (e.g. 11 for 352px)
var sx = (index % cols) * TILE;                  // column of the tile in the tileset
var sy = Math.floor(index / cols) * TILE;        // row of the tile in the tileset
ctx.drawImage(tileset, sx, sy, TILE, TILE, col * TILE, row * TILE, TILE, TILE);
```

An id is **not** a pixel coordinate.

**Map array.** `mapArray[row][column]`. The outer loop is the row (`i`, vertical), the inner loop the column (`j`, horizontal). Cell origin: `x = column * TILE`, `y = row * TILE`.

**Camera and scrolling.**

```
screenX = worldX - cameraX          screenY = worldY - cameraY
```

Course example: object at world (96, 64), camera at (64, 32), so it is drawn at (32, 32). Moving the camera changes the view, never the world position.

```js
camera.x = player.x + player.w/2 - canvas.width/2;                    // center on the player
camera.x = Math.max(0, Math.min(camera.x, WORLD_W - canvas.width));   // do not leave the map
```

For the TP, scrolling with the arrows is simply `cameraX += step` (with a clamp) and redraw. Only draw the visible cells: `firstCol = floor(camX / TILE)`, `lastCol = firstCol + ceil(canvas.width / TILE)`, and keep partly visible cells at the borders.

**Collision with tiles (logical grid).** Convert the position to a cell with `Math.floor(x / TILE)`. Test the cells under the corners of the character. Move axis by axis: try the new X, keep it only if free; then try the new Y. See `hitsSolid` in `04`.

---

## 6. Isometric (PW3)

Tile drawn as a diamond. Grid index `(i, j)` with `i` = row, `j` = column. Tile width `w`, map height `h` (**half the real tile height**, as the TP says):

```
x = (i - j) * w / 2 + offsetX
y = (i + j) * h / 2
offsetX = (nbColumns - 1) * w / 2        // so the left-most tile starts at x = 0
```

Course check: `i=2, j=1, w=64, h=32` gives `(32, 48)` before offsets.

- **Drawing order**: `i` loop outside, `j` loop inside (back to front). A tile drawn later covers tiles drawn before. Draw the character right after his own tile so tiles in front of him hide his feet correctly.
- **Scrolling**: subtract the camera (`x - camX`, `y - camY`), same as orthogonal. Map size in pixels: `width = (cols + rows) * w / 2`, `height = (cols + rows) * h / 2 + (tileRealHeight - h)`.
- **Mouse to tile (inverse)**, from the tile *centre*:
  `i - j = (mx - offsetX - w/2) / (w/2)`, `i + j = (my - h/2) / (h/2)`, then `i = (sum + diff) / 2`, `j = (sum - diff) / 2`, rounded. See `toGrid` in `05`.
- **Character on a tile**: put his feet on the middle of the diamond: `y_sprite = tileY + h/2 - spriteHeight`.
- **Arrow keys in the TP**: Down `i++` (down-right), Up `i--` (up-left), Left `j++` (down-left), Right `j--` (up-right). If the exam says another convention, follow the exam: the point is that each key changes `i` or `j`, not x or y.
- Isometric is a drawing trick: it does not make a 3D scene.

In Tiled: choose **Isometric** orientation, CSV layer format, tile size equal to the tileset tile size.

---

## 7. Physics with Box2DWeb (PW4, chapter 3)

**Hierarchy: World > Body > Fixture > Shape.**

| Object | Role |
|---|---|
| `b2World(gravity, allowSleep)` | owns everything, simulates, applies gravity |
| `b2BodyDef` then `b2Body` | position, angle, velocity, **type**: static / dynamic / kinematic |
| `b2FixtureDef` then fixture | **material**: density, friction, restitution (+ the shape) |
| `b2PolygonShape` / `b2CircleShape` | geometry only |

Body types: **static** never moves (floor, walls, platforms); **dynamic** reacts to gravity, forces and collisions (balls, crates); **kinematic** moves by code only, not by forces (moving platforms).

**Recipe (same 5 lines every time):**

```js
var def = new b2BodyDef();
def.type = b2Body.b2_dynamicBody;                 // or b2_staticBody
def.position.Set(x / scale, y / scale);           // CENTRE of the body, in METERS
var shape = new b2PolygonShape(); shape.SetAsBox(w/2 / scale, h/2 / scale);   // HALF sizes
// or: var shape = new b2CircleShape(r / scale);
fixDef.shape = shape;
world.CreateBody(def).CreateFixture(fixDef);
```

**Rules to remember**

- Units: meters, kilograms/tonnes, seconds (MTS). `scale` = pixels per meter (the TP uses 20, so 1 m = 20 px). Convert every length: `/ scale` going in, `* scale` coming out.
- Position is the **centre**. `SetAsBox` takes **half** width and **half** height.
- `gravity = new b2Vec2(0, 10)`: positive y points **down**, like the canvas.
- `world.Step(1/60, 10, 10)`: time step, velocity iterations, position iterations. Call once per frame, inside the game loop.
- Box2D draws nothing by itself. You draw canvas shapes at `body.GetPosition()` (meters * scale) with rotation `body.GetAngle()` (radians). Or use `b2DebugDraw` for debugging.
- Material: `density` gives mass (`mass = density * area`), `friction` 0 to 1, `restitution` (bounce) 0 = no rebound, 1 = full rebound.
- Shortcuts at the top of the file (`var Vec2 = Box2D.Common.Math.b2Vec2;` ...) as in the demo. The course files are in `../../COURS/Chapter3-Demo/`, your solution in `../PW4/`.

**Collision detection with a listener (PW4):**

```js
var listener = new Box2D.Dynamics.b2ContactListener();
listener.BeginContact = function (contact) { /* two fixtures started touching */ };
listener.EndContact   = function (contact) { /* they stopped touching */ };
// also: PreSolve (before the solver), PostSolve (after, has impulses)
world.SetContactListener(listener);
```

- Create the listener after the world and register it **once**.
- Who collided: `contact.GetFixtureA().GetBody()` and `contact.GetFixtureB().GetBody()`. To recognise a body, give it data: `body.SetUserData("hero")` then `body.GetUserData()`.
- Use a **counter** (`++` on Begin, `--` on End) for "is anything touching", as in your `PW4/main.js`. Setting a boolean in Begin and false in End fails when two contacts overlap.
- **Never create or destroy bodies inside a contact callback** (the world is locked during `Step`). Set a flag and destroy after `Step`, as `PW4/main.js` does for bodies that fall out of the scene.

**Useful extras:** `body.ApplyImpulse(new b2Vec2(x, y), body.GetWorldCenter())` (instant push), `body.ApplyForce(...)` (continuous), `body.SetLinearVelocity(new b2Vec2(vx, vy))`, `body.GetLinearVelocity()`, `world.DestroyBody(body)`, `world.ClearForces()` after `Step`.

**Why a physics engine.** Writing the maths yourself means detection, resolution, rotation, friction and so on. The engine runs the cycle for you each step: apply forces, detect collisions, resolve them, update position, velocity and rotation.

---

## 8. Collisions by hand (chapter 3)

```js
// rectangle vs rectangle (AABB): overlap on X and on Y
a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y

// circle vs circle: distance between centres < r1 + r2   (compare squares, no sqrt)
dx*dx + dy*dy < (r1 + r2) * (r1 + r2)

// circle vs rectangle: closest point of the rectangle, then distance
nx = clamp(c.x, r.x, r.x + r.w);  ny = clamp(c.y, r.y, r.y + r.h);
(c.x-nx)*(c.x-nx) + (c.y-ny)*(c.y-ny) < c.r * c.r

// point in rectangle (click on a button)
px >= r.x && px <= r.x + r.w && py >= r.y && py <= r.y + r.h
```

Game patterns:

- **Collectibles**: loop backwards over the array and `splice(i, 1)` the one touched (so the indices do not shift under you).
- **Damage with cooldown**: after a hit set `invincible = 1.5` seconds, else you lose all lives in 3 frames.
- **Bounce on a wall**: `if (x < 0 || x + w > canvas.width) vx = -vx;`

**Theory.**

- Testing all pairs of `n` objects is **O(n^2)**.
- Two phases: **broad phase** (cheap bounding volumes: AABB, OBB, circle, sphere; grids, quadtrees, BVH, sweep and prune) gives candidate pairs; **narrow phase** (precise: SAT, GJK) gives contact, normal and penetration depth. The worst case stays O(n^2), but in practice the broad phase removes most tests.
- **SAT**: two convex shapes are disjoint if some axis exists where their projections do not overlap.
- **Tunneling**: a fast object passes through a thin wall between two steps because only discrete positions are tested. Fix: continuous collision detection (CCD), smaller time step, or thicker walls.

---

## 9. Theory questions with short answers

**Chapter 1: design**

1. **Game design vs game development?** Design defines rules, actions, goals, difficulty, experience. Development builds it: code, art, audio, engine, integration, tests.
2. **Gameplay loop vs game loop?** Gameplay loop = player motivation cycle (objective, challenge/action, result/reward, new objective). Game loop = technical cycle (input, update, draw) of the program.
3. **What are the 3C?** Camera, Controls, Character. They must work together.
4. **Playtesting vs debugging?** Playtesting evaluates experience, difficulty, understanding and controls with varied players. Debugging finds and fixes technical defects. They complement each other.
5. **What is a GDD and what does it contain?** Reference document of the whole game. Sections: overview (title, genre, audience, platform, goal, originality), mechanics (actions, rules, resources, win/lose), game intelligence (enemy/NPC/environment reactions), game elements (characters, items, levels, sounds, animations, UI), story, progression (missions, difficulty, rewards, unlocks), menus and systems (start, pause, options, save). It describes how the player acts and how the system reacts, not only a story.
6. **How does brainstorming work?** Generate many ideas first: defer judgement, favour quantity, welcome unusual ideas, build on others'. Select afterwards using the target experience and constraints (time, team, tools).
7. **Tool categories?** Game engine, IDE, drawing and animation, 3D modelling, audio, version control, testing and profiling.
8. **Why is difficulty not automatically unfair?** The player must understand their options and why they failed.

**Chapter 2: sprites, tiles**

9. **Sprite vs tile?** A sprite is an independent visual object (character, enemy). A tile is a small reusable piece of the decor that belongs to a grid.
10. **Why separate visual grid and logical grid?** Changing a texture must not change the rules (solid, danger, passage) by accident.
11. **Why subtract the camera?** To convert a world position to a screen position. The object does not move in the world.
12. **Frames in a 320 px wide row with 32 px frames?** 10. A 320 x 96 sheet has 10 columns and 3 rows.
13. **Animation at one frame every 100 ms?** 10 frames per second, independent of the screen refresh rate, if you use elapsed time.
14. **Why draw only visible tiles?** Less rendering work. Include partly visible tiles at the borders.
15. **Is isometric 3D?** No. It is a 2D projection of a grid that looks like depth.

**Chapter 3: physics**

16. **Rigid body?** Keeps its shape and size under forces; moves by translation and rotation. Properties: size, mass, position, velocity, acceleration, restitution.
17. **Key formulas?** `p_new = p + v * dt`, `F = m * a`, `F_g = m * g`.
18. **Engine cycle each step?** Apply forces, detect collisions, resolve collisions, update position/velocity/rotation.
19. **Examples of engines?** 2D: Box2D, Box2DWeb, Matter.js. 3D: PhysX, Bullet.
20. **Why is `SetAsBox(200/scale, 20/scale)` a 400 x 40 px rectangle?** It takes half sizes.

---

## 10. Drills (do them on a blank page, with a timer)

Each drill states a target time. Check yourself against the matching template.

1. **(5 min)** Canvas 500x300. Draw a red rectangle, a blue circle with a black border, the text "Hello" and a line. *(01)*
2. **(8 min)** A square moves with arrows at 200 px/s, stays inside the canvas, and changes colour while Space is held. *(02)*
3. **(10 min)** Given `sheet.png` with 6 frames of 48x48 in one row: display the whole sheet, then the first frame, then animate it at 8 frames per second at the centre of the canvas. *(03)*
4. **(10 min)** Same as 3 but the sheet has 2 rows (left/right). The character walks with the arrows and faces the direction of travel. *(03)*
5. **(15 min)** Given a 10 x 5 `mapArray` and a tileset of 3 tiles (32 px): draw the map. Then shrink the canvas to 160x96 and scroll with the arrows, clamped to the map. *(04)*
6. **(15 min)** Add a character that moves in the scrolling map, the camera centred on him, and tiles with id 2 are walls he cannot enter. *(04)*
7. **(15 min)** Isometric: draw a 6x6 map from a 2D array using diamond tiles (`w = 64`, `h = 32`). Highlight the tile under the mouse. *(05)*
8. **(20 min)** Box2D: a static floor, a dynamic circle that falls and bounces (restitution 0.6), and the text "Collision!" in red while touching. *(06)*
9. **(10 min)** Box2D: click on the canvas to spawn a circle or box at the mouse. Remove bodies that fall below the canvas. *(06)*
10. **(25 min)** A full game without a library: player (arrows), 5 coins to collect, 3 bouncing enemies, 3 lives, score, game over screen with restart. *(08)*

---

## 11. Debugging checklist (when "nothing shows")

1. Open the console (F12). A red error stops everything. Most common: typo in an id, `ctx` used before it is defined, missing `)`.
2. `getElementById` returned `null`? The script runs before the canvas exists. Put the `<script>` after the `<canvas>`, or use `onload`.
3. Image not showing: wrong path, file opened with a path that does not match case, or `drawImage` called before `onload`.
4. File opened by double-click (`file://`): `fetch` / loading `.csv` with Ajax is blocked by the browser. Embed the array in the JS (as in `TP3/isometric_map.html`) or use a local server (`python -m http.server`).
5. Everything draws on top of itself: forgot `clearRect` at the start of `draw`.
6. Movement ignores your key: you test `e.key` strings wrongly (`"ArrowLeft"`, not `"Left"`), or the page does not have focus (click it once).
7. Box2D object invisible or in the wrong place: forgot `/ scale` or `* scale`; forgot `Step`; position is the centre; `SetAsBox` takes half sizes.
8. Box2D "falls through" the floor: floor created as dynamic instead of static, or object too fast (tunneling).
9. Shape drawn with an unexpected colour/rotation: missing `ctx.save()/restore()` around the transforms.
10. `ctx.rotate` seems to do nothing or spins wildly: angle must be in **radians**.

---

## 12. Exam-day plan

1. Read the whole sheet first. Note what is asked and what is **not** (nothing more, nothing less).
2. Type the skeleton (section 1) before anything else. Get a coloured rectangle on screen in the first 5 minutes.
3. Add one feature at a time and test after each. Never write 100 lines blind.
4. Comment briefly while you write: it helps you and the grader.
5. If the exam gives you assets (spritesheet, tileset, CSV, `Box2d.min.js`), first check their sizes and layout: frame size, rows = directions, tile size, id convention. Most mistakes come from wrong assumptions here.
6. Leave 5 minutes to run it from a clean refresh and check the console.
