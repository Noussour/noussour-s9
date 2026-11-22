// ============================================================================
// sound.js: sound effects for version 2, made with the Web Audio API
// (no sound files: every effect is generated with oscillators and noise)
//
// AI USED: this file was written with Claude Code (AI assistant).
// Prompt used: "improve on it so when clicking 2 an entirely new version of the
//   game is shown with scores nice interface use of 3 birds [...] and sound effects"
// ============================================================================

var Sound = (function () {
    var ac = null;        // AudioContext, created on the first click or key press
    var master = null;    // master volume
    var muted = false;
    var noiseBuffer = null;

    function audio() {
        if (!ac) {
            var AC = window.AudioContext || window.webkitAudioContext;
            if (!AC) return null;
            ac = new AC();
            master = ac.createGain();
            master.gain.value = 0.5;
            master.connect(ac.destination);
            // one second of white noise, reused by every noisy effect
            noiseBuffer = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
            var d = noiseBuffer.getChannelData(0);
            for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
        }
        if (ac.state === "suspended") ac.resume();
        return ac;
    }

    // a tone: frequency (Hz), duration (s), wave type, volume, optional slide and delay
    function tone(freq, dur, type, vol, slideTo, delay) {
        var a = audio();
        if (!a || muted) return;
        var t = a.currentTime + (delay || 0);
        var o = a.createOscillator();
        var g = a.createGain();
        o.type = type || "sine";
        o.frequency.setValueAtTime(freq, t);
        if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(vol || 0.3, t + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        o.connect(g);
        g.connect(master);
        o.start(t);
        o.stop(t + dur + 0.05);
    }

    // filtered noise: crashes, cracks, whooshes
    function noise(dur, vol, filterType, freq, freqTo, delay) {
        var a = audio();
        if (!a || muted) return;
        var t = a.currentTime + (delay || 0);
        var src = a.createBufferSource();
        src.buffer = noiseBuffer;
        var f = a.createBiquadFilter();
        f.type = filterType;
        f.frequency.setValueAtTime(freq, t);
        if (freqTo) f.frequency.exponentialRampToValueAtTime(freqTo, t + dur);
        var g = a.createGain();
        g.gain.setValueAtTime(vol, t);
        g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        src.connect(f);
        f.connect(g);
        g.connect(master);
        src.start(t);
        src.stop(t + dur + 0.05);
    }

    var lastHit = 0;

    return {
        unlock: audio,
        toggleMute: function () { muted = !muted; return muted; },
        isMuted: function () { return muted; },

        stretch: function () { tone(220, 0.3, "triangle", 0.12, 520); },
        launch: function () {
            noise(0.4, 0.5, "bandpass", 2500, 300);
            tone(600, 0.3, "sine", 0.08, 180);
        },
        // impact: strength decides the volume, limited to one every 70 ms
        hit: function (strength) {
            var now = Date.now();
            if (now - lastHit < 70) return;
            lastHit = now;
            noise(0.15, Math.min(0.6, 0.08 + strength * 0.04), "lowpass", 700, 120);
        },
        breakBlock: function (material) {
            if (material === "ice") {
                noise(0.35, 0.4, "highpass", 5000, 2500);
                tone(2100, 0.15, "sine", 0.07, 1200);
                tone(1500, 0.2, "sine", 0.06, 900, 0.05);
            } else if (material === "rock") {
                noise(0.5, 0.7, "lowpass", 500, 60);
                tone(90, 0.3, "square", 0.08, 50);
            } else {
                noise(0.3, 0.6, "bandpass", 1400, 250);
                tone(170, 0.15, "square", 0.07, 90);
            }
        },
        pig: function () {
            tone(520, 0.1, "square", 0.1, 380);
            tone(470, 0.14, "square", 0.1, 300, 0.12);
        },
        newBird: function () { tone(500, 0.1, "sine", 0.15, 900); },
        poof: function () { noise(0.25, 0.25, "bandpass", 900, 3000); },
        star: function (i, delay) { tone(880 * Math.pow(1.26, i), 0.35, "triangle", 0.25, null, delay); },
        win: function () {
            [523, 659, 784, 1047].forEach(function (f, i) { tone(f, 0.3, "triangle", 0.22, null, i * 0.12); });
        },
        lose: function () {
            [392, 330, 262, 196].forEach(function (f, i) { tone(f, 0.35, "sawtooth", 0.1, null, i * 0.2); });
        }
    };
})();
