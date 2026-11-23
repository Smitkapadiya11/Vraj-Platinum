// Solar position (NOAA / SunCalc formulation) — returns altitude & azimuth in radians.
// azimuth measured from North, clockwise (0 = N, π/2 = E).
const rad = Math.PI / 180;
const dayMs = 86400000, J1970 = 2440588, J2000 = 2451545;
const e = rad * 23.4397;
const toDays = (d: Date) => d.valueOf() / dayMs - 0.5 + J1970 - J2000;
const solarMeanAnomaly = (d: number) => rad * (357.5291 + 0.98560028 * d);
function eclipticLongitude(M: number) {
  const C = rad * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
  return M + C + rad * 102.9372 + Math.PI;
}
export function sunPosition(date: Date, lat: number, lng: number) {
  const lw = rad * -lng, phi = rad * lat, d = toDays(date);
  const M = solarMeanAnomaly(d), L = eclipticLongitude(M);
  const dec = Math.asin(Math.sin(e) * Math.sin(L));
  const ra = Math.atan2(Math.sin(L) * Math.cos(e), Math.cos(L));
  const th = rad * (280.16 + 360.9856235 * d) - lw;
  const H = th - ra;
  const alt = Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
  const azS = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi));
  return { altitude: alt, azimuth: azS + Math.PI };
}
/** Date for today at a given local IST hour (Surat is UTC+5:30). */
export function istDate(hour: number, base = new Date()) {
  const d = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth(), base.getUTCDate(), 0, 0, 0));
  return new Date(d.valueOf() + (hour - 5.5) * 3600000);
}
