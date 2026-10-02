// Pure numeric track. In Remotion call valueAt(track, useCurrentFrame() / fps).
const clamp = (x) => Math.max(0, Math.min(1, x));
const easing = {
  linear: (p) => p,
  smooth: (p) => p*p*p*(p*(p*6-15)+10),
  easeIn: (p) => p*p*p,
  easeOut: (p) => 1-Math.pow(1-p, 3),
};
export function valueAt(keys, seconds) {
  if (!Number.isFinite(seconds) || keys.length===0) throw Error('Finite time and keyframes required');
  for (let i=0; i<keys.length; i++) {
    if (!Number.isFinite(keys[i].time) || !Number.isFinite(keys[i].value) || (i && keys[i].time<=keys[i-1].time)) throw Error('Keyframes must have finite values and strictly increasing times');
  }
  if (seconds<=keys[0].time) return keys[0].value;
  for(let i=1; i<keys.length; i++) {
    const a=keys[i-1], b=keys[i];
    if(seconds<=b.time) {
      const ease=easing[a.ease ?? 'smooth'];
      if(!ease) throw Error('Unsupported easing');
      return a.value+(b.value-a.value)*ease(clamp((seconds-a.time)/(b.time-a.time)));
    }
  }
  return keys[keys.length-1].value;
}
// Stable entrance, pause and exit; seconds work at either 30 or 60 fps.
export const entranceHoldExit = [
  {time:0, value:80, ease:'smooth'},
  {time:.35, value:0, ease:'linear'},
  {time:1.6, value:0, ease:'smooth'},
  {time:2, value:-60},
];
