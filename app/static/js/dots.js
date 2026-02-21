/* Interactive dot-grid background */
(function(){
  const cv = document.getElementById('bg-canvas');
  const ctx = cv.getContext('2d');

  let W, H;
  const SPACING = 40;
  const BASE_RADIUS = 1.5;
  const MOUSE_RADIUS = 150;
  const PUSH_STRENGTH = 25;

  let mouseX = -9999, mouseY = -9999;
  let active = false;
  let pulsePhase = 0;
  let activeAmount = 0; // 0=idle, 1=fully active — smoothly interpolated

  let dots = [];

  function buildGrid(){
    dots = [];
    const cols = Math.ceil(W / SPACING) + 1;
    const rows = Math.ceil(H / SPACING) + 1;
    for(let r = 0; r < rows; r++){
      for(let c = 0; c < cols; c++){
        dots.push({
          homeX: c * SPACING,
          homeY: r * SPACING,
          x: c * SPACING,
          y: r * SPACING,
          offsetX: 0,
          offsetY: 0,
          phase: Math.random() * Math.PI * 2, // idle float phase
        });
      }
    }
  }

  function resize(){
    W = cv.width = window.innerWidth;
    H = cv.height = window.innerHeight;
    buildGrid();
  }

  window.addEventListener('resize', resize);
  resize();

  window.addEventListener('mousemove', function(e){
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  window.addEventListener('mouseleave', function(){
    mouseX = -9999;
    mouseY = -9999;
  });

  function draw(){
    ctx.clearRect(0, 0, W, H);

    // Smooth interpolation toward target
    const target = active ? 1 : 0;
    activeAmount += (target - activeAmount) * 0.06;
    pulsePhase += 0.03;

    // Breathing oscillation for active state
    const breath = 0.6 + Math.sin(pulsePhase * 1.8) * 0.4;
    // Ripple time for center-outward wave
    const cx = W / 2, cy = H / 2;
    const maxDist = Math.sqrt(cx * cx + cy * cy);

    for(let i = 0; i < dots.length; i++){
      const d = dots[i];

      // Idle floating motion
      d.phase += 0.008;
      const floatX = Math.sin(d.phase) * 2;
      const floatY = Math.cos(d.phase * 0.7) * 2;

      // Mouse interaction
      const dx = d.homeX - mouseX;
      const dy = d.homeY - mouseY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      let pushX = 0, pushY = 0, mouseBright = 0;

      if(dist < MOUSE_RADIUS && dist > 0){
        const force = (1 - dist / MOUSE_RADIUS) * PUSH_STRENGTH;
        pushX = (dx / dist) * force;
        pushY = (dy / dist) * force;
        mouseBright = 1 - dist / MOUSE_RADIUS;
      }

      // Smooth offset
      d.offsetX += (pushX + floatX - d.offsetX) * 0.15;
      d.offsetY += (pushY + floatY - d.offsetY) * 0.15;
      d.x = d.homeX + d.offsetX;
      d.y = d.homeY + d.offsetY;

      // Skip offscreen
      if(d.x < -20 || d.x > W + 20 || d.y < -20 || d.y > H + 20) continue;

      // Color: idle grey -> orange when active, ripple from center
      const distFromCenter = Math.sqrt(
        (d.homeX - cx) * (d.homeX - cx) + (d.homeY - cy) * (d.homeY - cy)
      );
      const rippleDelay = (distFromCenter / maxDist) * 2; // 0-2 seconds offset
      const rippleWave = Math.sin(pulsePhase * 2 - rippleDelay * Math.PI) * 0.5 + 0.5;
      const orangeAmount = activeAmount * rippleWave;

      // Base grey: #333 = rgb(51,51,51)
      // Orange: #ff6600 = rgb(255,102,0)
      const r = Math.round(51 + (255 - 51) * orangeAmount);
      const g = Math.round(51 + (102 - 51) * orangeAmount);
      const b = Math.round(51 - 51 * orangeAmount);

      // Radius: base + mouse proximity growth + active pulsation
      let radius = BASE_RADIUS;
      radius += mouseBright * 2; // grow near cursor
      radius += activeAmount * breath * 1.2; // pulsate when active

      // Alpha
      let alpha = 0.4 + mouseBright * 0.5 + activeAmount * breath * 0.3;
      alpha = Math.min(alpha, 1);

      ctx.beginPath();
      ctx.arc(d.x, d.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
      ctx.fill();
    }

    requestAnimationFrame(draw);
  }

  draw();

  window.bgPulse = function(isActive){
    active = isActive;
  };
})();
