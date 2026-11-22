# Practical Midterm (Box2DWeb slingshot game) - Walid BECHAR

Statement: `../Test/test.pdf`

Two versions of the same game, both using the provided `sprites/` and `materials/`.

| File | What it is |
|------|------------|
| `simple.html` | Straight to the point: exactly the 7 requirements, short and commented. This is the one to hand in. |
| `beautiful.html` | Same requirements plus a polished game: 3 birds, score, stars, debris, sounds, "How to play" screen. |

## How to run

Open `simple.html` or `beautiful.html` in a browser (double click). Nothing to install.

## How to play

1. Press on the red bird in the slingshot.
2. Drag backwards to aim: the farther you pull, the stronger the shot. Dots preview the path.
3. Release to launch.
4. Knock the target off the tower. When it touches the ground the message changes from
   "No targets on the ground yet" to "Bravo !".
5. Restart at any time with the **Restart (R)** button or the **R** key ("Play again" after a win).

## Requirements map (`simple.html`)

Each part is marked in the code with the same number as in the statement.

| # | Requirement | Where in the code |
|---|-------------|-------------------|
| 1 | Box2D world with gravity + static ground | `buildLevel()`: `new b2World(new b2Vec2(0, 9.8), true)` and a static ground box |
| 2 | Dynamic player (bird) and target (pig) | `buildLevel()`: both dynamic **circle** bodies |
| 3 | At least 5 obstacles | `buildLevel()`: 9 dynamic **box** bodies (2 level tower + blocks) |
| 4 | Sprites follow position and rotation | `drawBody()`: `translate` to the body centre, `rotate(GetAngle())`, `drawImage` centred |
| 5 | Launch by click and drag | pointer events: `velocity = (slingshot - pull) * POWER`, then `SetLinearVelocity` |
| 6 | Detect target touching the ground + message | `b2ContactListener.BeginContact` checks pig + ground, `drawMessage()` shows "Bravo !" |
| 7 | Side walls | `buildLevel()`: two static boxes on the left and right edges |

Game loop: `requestAnimationFrame` with a fixed 1/60 s physics step (`world.Step(DT, 10, 10)`).

## AI usage

As required by the statement, the comment block at the top of each script lists the AI tool and the prompts used.
