"""Eased trip-time model for the HT-04 on the station haul paths (Coder's speed plan, 10/23):
   8.33 m/s (30 km/h) on straights, 4.0 m/s through turns, accelerate 3.0 m/s2, brake 4.0 m/s2, reverse capped at 3.0 m/s.
   Forward/backward pass over 5 cm steps (the classic speed-profile solve), so every speed change is eased, never a step.
   python3 haul_times.py INFO.json  (build_*.py *_info.json with 'haul' legs) or import and call trip()."""
import json, sys, math
V_STRAIGHT, V_TURN, ACC, BRK, V_REV = 100 / 12, 4.0, 3.0, 4.0, 3.0
def trip(legs, v0=0.0, v1=0.0, ds=0.05):
    """legs: [(name, length_m, vmax)]. Returns (total_s, [(name, t_s, v_in, v_out)])."""
    xs, vm, nm = [], [], []
    for n, L, v in legs:
        k = max(1, int(round(L / ds)))
        for _ in range(k): xs.append(L / k); vm.append(v); nm.append(n)
    N = len(xs); v = [0.0] * (N + 1)
    v[0] = min(v0, vm[0]); lim = [min(vm[max(0, i - 1)], vm[min(N - 1, i)]) for i in range(N + 1)]; lim[0] = v[0]; lim[N] = v1
    for i in range(N): v[i + 1] = min(lim[i + 1], math.sqrt(v[i] ** 2 + 2 * ACC * xs[i]))
    for i in range(N - 1, -1, -1): v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * BRK * xs[i]))
    out, tot, cur, t_, vin = [], 0.0, nm[0], 0.0, v[0]
    for i in range(N):
        if nm[i] != cur: out.append((cur, t_, vin, v[i])); cur, t_, vin = nm[i], 0.0, v[i]
        dt = 2 * xs[i] / max(1e-6, v[i] + v[i + 1]); t_ += dt; tot += dt
    out.append((cur, t_, vin, v[N]))
    return tot, out
def fmt(title, tot, out):
    s = ['%s: %.2f s' % (title, tot)] + ['   %-34s %5.2f s  (%.1f -> %.1f m/s)' % (n, t, a, b) for n, t, a, b in out]
    return '\n'.join(s)
if __name__ == '__main__':
    I = json.load(open(sys.argv[1])); H = I['haul']
    print(json.dumps(H.get('times', {}), indent=1))
