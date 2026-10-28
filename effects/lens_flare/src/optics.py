"""Lens Flare's optics, in plain Python: which ghosts a lens throws, where, how big and how bright, in each color.

After Lee and Eisemann, "Practical Real-Time Lens-Flare Rendering" (EGSR 2013): paraxial (first-order) optics, where a
ray is its height y and slope u, and each thing that happens to it is a 2 x 2 ray transfer matrix. A ghost is light that
reflects twice inside the lens, off surface j and then back off surface i (i < j), and so reaches the sensor where it
shouldn't. Both reflections are on one side of the iris (the paper's restriction: otherwise the light would cross the
iris three times). Its matrix splits into Ma, from the front of the lens to the iris, and Ms, from the iris to the
sensor. A light at slope theta reaches the iris at y_a = Ma11 h + Ma12 theta, so the rays that pass are the iris's shape,
and on the sensor that shape lands at y_s = S y_a + theta Ms12 / Ma11, with S = Ms11 + Ms12 Ma21 / Ma11 (det Ma = 1 for
a path from air to air with an even number of reflections). So every ghost is the iris's shape, scaled by S and placed
on the line from the light through the middle of the picture, at a fixed multiple of the light's offset.

Everything here is linear in the light's position: a ghost is the iris's shape at position c p and size rho (p the
light's position from the picture's middle), cut by the front element (the entrance pupil, as the paper does), and as
bright as the light's energy times R_i R_j over its area. No table of precomputed shapes: each ghost is these few numbers.

Coordinates in the picture are in units of its half diagonal, which stands for the lens's image height at the edge of
its field. Colors are the paper's three wavelengths (650, 510 and 475 nm), with each glass's index from its n_d and
Abbe number (a two-term Cauchy formula through n_F - n_C = (n_d - 1) / V_d).
"""
import math

WAVELENGTHS = (650.0, 510.0, 475.0)       # nm: red, green, blue (Lee and Eisemann)
LINES = (486.1327, 587.5618, 656.2725)    # nm: the F, d and C lines that define the Abbe number


def index(nd, vd, lam):
    """A glass's refractive index at lam nm from its n_d and V_d (air: 1)."""
    if vd <= 0:
        return nd
    f, d, c = LINES
    b = (nd - 1.0) / vd / (1.0 / f ** 2 - 1.0 / c ** 2)
    return nd + b * (1.0 / lam ** 2 - 1.0 / d ** 2)


def mul(a, b):
    return ((a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]),
            (a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]))


I2 = ((1.0, 0.0), (0.0, 1.0))


def travel(dz):
    """Along the axis by dz (negative going backward), slope unchanged."""
    return ((1.0, dz), (0.0, 1.0))


def refract(radius, n1, n2):
    """Through a spherical surface from index n1 into n2, either way along the axis: n2 u2 = n1 u1 - y (n2 - n1) / R."""
    power = 0.0 if radius == 0 else (n1 - n2) / (n2 * radius)
    return ((1.0, 0.0), (power, n1 / n2))


def reflect(radius):
    """Off a spherical surface, either side: the slope mirrors about the surface's normal (slope -y / R)."""
    return ((1.0, 0.0), (0.0 if radius == 0 else -2.0 / radius, -1.0))


class Lens:
    """A lens's surfaces at one wavelength: positions along the axis, radii, indices (n[k] before surface k, n[k + 1]
    after it), clear radii, which one is the iris."""

    def __init__(self, spec, lam):
        self.radius, self.z, self.n, self.clear = [], [], [1.0], []
        z = 0.0
        for k, s in enumerate(spec['surfaces']):
            self.radius.append(s[0])
            self.z.append(z)
            self.n.append(index(s[2], s[3], lam))
            self.clear.append(s[4])
            if len(s) > 5:
                self.stop = k
            z += s[1]
        self.sensor = z
        self.last = len(self.radius) - 1

    def trace(self, start, events, end):
        """The matrix of a path starting at z = start: events are (surface, 'f' through it going forward, 'b' through
        it going backward, 'r' reflecting off it), travelling between them, ending at z = end."""
        m, z = I2, start
        for k, what in events:
            m = mul(travel(self.z[k] - z), m)
            z = self.z[k]
            if what == 'f':
                m = mul(refract(self.radius[k], self.n[k], self.n[k + 1]), m)
            elif what == 'b':
                m = mul(refract(self.radius[k], self.n[k + 1], self.n[k]), m)
            else:
                m = mul(reflect(self.radius[k]), m)
        return mul(travel(end - z), m)

    def bounce(self, i, j):
        """Forward to surface j, reflect, backward to surface i, reflect: the events between the two passes."""
        return ([(k, 'f') for k in range(j)] + [(j, 'r')] + [(k, 'b') for k in range(j - 1, i, -1)] + [(i, 'r')],
                i + 1)

    def direct(self):
        """The intended path: (Ma, the front to the iris; Mf, the front to the sensor)."""
        ma = self.trace(self.z[0], [(k, 'f') for k in range(self.stop)], self.z[self.stop])
        mf = self.trace(self.z[0], [(k, 'f') for k in range(self.last + 1)], self.sensor)
        return ma, mf

    def ghost(self, i, j):
        """The path reflecting off surface j and then surface i, both on one side of the iris: (Ma, the front to the
        iris; Ms, the iris to the sensor)."""
        s = self.stop
        if j < s:
            events, resume = self.bounce(i, j)
            ma = self.trace(self.z[0], events + [(k, 'f') for k in range(resume, s)], self.z[s])
            ms = self.trace(self.z[s], [(k, 'f') for k in range(s, self.last + 1)], self.sensor)
        else:
            ma = self.trace(self.z[0], [(k, 'f') for k in range(s)], self.z[s])
            events, resume = self.bounce(i, j)
            events = [e for e in events if e[0] >= s or e[1] != 'f']
            ms = self.trace(self.z[s], events + [(k, 'f') for k in range(resume, self.last + 1)], self.sensor)
        return ma, ms


def reflectance(n1, n2, layers, lam):
    """How much light a surface between indices n1 and n2 reflects at lam nm and normal incidence, under thin-film
    layers [(index, optical thickness in nm), ...] from the n1 side (Macleod's characteristic matrices; none: bare
    glass, Fresnel's ((n1 - n2) / (n1 + n2))^2)."""
    if n1 == n2:
        return 0.0
    # [B, C] = prod [[cos d, i sin d / n], [i n sin d, cos d]] [1, n2]; r = (n1 B - C) / (n1 B + C).
    br, bi, cr, ci = 1.0, 0.0, n2, 0.0
    for n, optical in reversed(layers):
        d = 2.0 * math.pi * optical / lam
        cs, sn = math.cos(d), math.sin(d)
        br, bi, cr, ci = (cs * br - sn / n * ci, cs * bi + sn / n * cr,
                          cs * cr - n * sn * bi, cs * ci + n * sn * br)
    nr, ni = n1 * br - cr, n1 * bi - ci
    dr, di = n1 * br + cr, n1 * bi + ci
    return (nr * nr + ni * ni) / (dr * dr + di * di)


def coating_layers(kind, k, n1, n2):
    """The coating on surface k (layers from the air side, as reflectance() takes them). bare: none. single: one
    quarter wave of magnesium fluoride (1.38), as lenses were coated from the 1940s, tuned near 550 nm. multi: a
    quarter-half-quarter broadband coating (magnesium fluoride, zirconia 2.05, alumina 1.62), as multicoated lenses
    have. Each surface's tuning moves a little (with k), as a maker's batches and the light's angle would."""
    if kind == 'bare':
        return []
    tune = 550.0 + 45.0 * math.sin(2.4 * k + 0.7)
    glass_first = n1 > n2                     # the layers sit on the glass, the air on the other side
    if kind == 'single':
        layers = [(1.38, tune / 4.0)]
    else:
        layers = [(1.38, tune / 4.0), (2.05, tune / 2.0), (1.62, tune / 4.0)]
    return list(reversed(layers)) if glass_first else layers


COATINGS = ('bare', 'single', 'multi')


def ghosts(spec, fnumber=None):
    """Every ghost of the lens (pairs i < j on one side of the iris), at each wavelength: a list of dicts with
    i, j and per channel (red, green, blue) c (position: a multiple of the light's offset), rho (the iris's image's
    size, in picture units: its corners' distance from its middle, negative where it is upside down), clip (the front element's circle in the iris's units: center as a multiple of the
    light's offset, and radius), bright (the ghost's brightness per unit of the light's energy, before reflectances) and
    refl (R_i R_j, per coating in COATINGS). fnumber defaults to the lens's own."""
    fnumber = fnumber or spec['fnumber']
    lenses = [Lens(spec, lam) for lam in WAVELENGTHS]
    surfaces = len(spec['surfaces'])
    out = []
    for j in range(surfaces):
        for i in range(j):
            if i < lenses[0].stop < j or lenses[0].stop in (i, j):
                continue
            g = dict(i=i, j=j, c=[], rho=[], clip_c=[], clip_r=[], bright=[], refl={})
            for lens, lam in zip(lenses, WAVELENGTHS):
                ma_d, mf = lens.direct()
                focal = mf[0][1]                      # y on the sensor = focal * theta for the intended image
                height = spec['image_height']
                r_stop = abs(ma_d[0][0]) * focal / (2.0 * fnumber)
                ma, ms = lens.ghost(i, j)
                big_s = ms[0][0] + ms[0][1] * ma[1][0] / ma[0][0]
                g['c'].append(ms[0][1] / (ma[0][0] * focal))
                g['rho'].append(big_s * r_stop / height)
                # Front element: |h| < clear[0], h = (y_a - Ma12 theta) / Ma11, theta = p height / focal.
                g['clip_c'].append(ma[0][1] * height / (focal * r_stop))
                g['clip_r'].append(lens.clear[0] * abs(ma[0][0]) / r_stop)
                # Energy through the iris on this path against the intended one, spread over the ghost's area.
                g['bright'].append((ma_d[0][0] / ma[0][0]) ** 2 / max(abs(big_s) * r_stop / height, 1e-6) ** 2)
            for kind in COATINGS:
                g['refl'][kind] = [surface_reflectance(lens, j, kind, lam) * surface_reflectance(lens, i, kind, lam)
                                   for lens, lam in zip(lenses, WAVELENGTHS)]
            out.append(g)
    return out


def surface_reflectance(lens, k, kind, lam):
    n1, n2 = lens.n[k], lens.n[k + 1]
    return reflectance(n1, n2, coating_layers(kind, k, n1, n2), lam)


def power(table, coating):
    """The share of a light's energy all the ghosts carry together with this coating (each ghost's R_i R_j times the
    light its path lets through the iris against the intended path's), averaged over the three colors."""
    total = 0.0
    for g in table:
        for ch in range(3):
            total += g['refl'][coating][ch] * g['bright'][ch] * g['rho'][ch] ** 2 / 3.0   # bright ~ 1 / rho^2
    return total
