// ============================================================================
// shell.js: what both versions share
//   - keys 1 and 2 switch between version 1 (midterm answer) and version 2
//   - key F puts the canvas in fullscreen (and back)
//   - canvasPoint(e): mouse position in canvas pixels, also correct in fullscreen
//   - resizeCanvas / applyView: sharp (not pixelated) drawing at any size
//
// AI USED: this file was written with Claude Code (AI assistant).
// Prompt used: "improve on it so when clicking 2 an entirely new version of the
//   game is shown [...] and also make it that when hitting f the canvas is in
//   full screen"
// ============================================================================

// Logical size of the game: both versions draw in this 800 x 450 space.
// The real canvas has more pixels (screen size x devicePixelRatio) so the
// picture stays sharp on big / high-density screens and in fullscreen.
var VIEW_W = 800, VIEW_H = 450;

function resizeCanvas() {
    var c = document.getElementById("canvas");
    var r = c.getBoundingClientRect();
    var s = Math.min(r.width / VIEW_W, r.height / VIEW_H);      // displayed size / logical size
    var k = s * (window.devicePixelRatio || 1);
    if (!isFinite(k) || k <= 0) k = 1;
    k = Math.min(k, 3);                                         // limit the cost on very big screens
    var w = Math.round(VIEW_W * k), h = Math.round(VIEW_H * k);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
}

// called at the start of each frame: draw in logical units, smooth image scaling
function applyView(ctx) {
    var c = ctx.canvas;
    ctx.setTransform(c.width / VIEW_W, 0, 0, c.height / VIEW_H, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
}

window.addEventListener("resize", resizeCanvas);
document.addEventListener("fullscreenchange", function () { setTimeout(resizeCanvas, 50); });
document.addEventListener("webkitfullscreenchange", function () { setTimeout(resizeCanvas, 50); });

var versions = {};     // versions[1], versions[2] = { start, stop }
var currentVersion = null;
var wantedVersion = 1;

// each version calls this once its images are loaded
function registerVersion(n, api) {
    versions[n] = api;
    if (n === wantedVersion && currentVersion === null) switchVersion(n);
}

function switchVersion(n) {
    wantedVersion = n;
    if (!versions[n] || n === currentVersion) return;     // not loaded yet, or already shown
    if (currentVersion !== null) versions[currentVersion].stop();
    resizeCanvas();
    currentVersion = n;
    versions[n].start();
    var b1 = document.getElementById("btn1"), b2 = document.getElementById("btn2");
    if (b1) b1.className = (n === 1) ? "on" : "";
    if (b2) b2.className = (n === 2) ? "on" : "";
}

// Mouse position in canvas pixels. In fullscreen the canvas is scaled to fit the
// screen while keeping its proportions (object-fit: contain), so black bands may
// appear on two sides: remove them, then divide by the scale.
function canvasPoint(e) {
    var c = document.getElementById("canvas");
    var r = c.getBoundingClientRect();
    var s = Math.min(r.width / VIEW_W, r.height / VIEW_H);
    var ox = r.left + (r.width - VIEW_W * s) / 2;
    var oy = r.top + (r.height - VIEW_H * s) / 2;
    return { x: (e.clientX - ox) / s, y: (e.clientY - oy) / s };
}

function toggleFullscreen() {
    var c = document.getElementById("canvas");
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        if (c.requestFullscreen) c.requestFullscreen();
        else if (c.webkitRequestFullscreen) c.webkitRequestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
    }
}

document.addEventListener("keydown", function (e) {
    if (typeof Sound !== "undefined") Sound.unlock();     // browsers allow sound only after a user action
    if (e.key === "1") switchVersion(1);
    if (e.key === "2") switchVersion(2);
    if (e.key === "f" || e.key === "F") toggleFullscreen();
});
document.addEventListener("mousedown", function () {
    if (typeof Sound !== "undefined") Sound.unlock();
});
