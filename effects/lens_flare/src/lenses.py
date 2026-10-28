"""The lenses Lens Flare can be: camera lenses from expired patents.

Each lens is its surfaces in order from the front, as (radius, thickness, n_d, V_d, semi_diameter) in mm: the radius of
curvature (0 for flat; positive bulges toward the front), the distance to the next surface (the last one's is to the
image), the glass after the surface by its refractive index at the d line (587.6 nm) and its Abbe number (1.0 and 0 for
air), and half the surface's clear diameter. STOP marks the iris. Each lens also gives its f-number as designed and its
image height at the edge of its field, which the picture's half diagonal stands for.

The prescriptions are from Nathan Hagen's LensLibrary (https://github.com/nzhagen/LensLibrary), transcribed there from
the patents named:

    Copyright (c) 2021 Nathan Hagen

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of
    the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
    THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

STOP = 'stop'

LENSES = {
    # A. W. Tronnier, US 2,645,156 (1953): Voigtlaender's Color-Heliar, the lens Lee and Eisemann's paper shows (its
    # Table 1). f/3.5, 100 mm.
    'heliar': dict(label='Heliar (1953)', fnumber=3.5, image_height=50.086, surfaces=(
        (30.81, 7.702, 1.6511, 58.6, 17.0),
        (-89.35, 1.849, 1.60266, 38.4, 17.0),
        (580.38, 3.521, 1.0, 0.0, 14.856),
        (-80.63, 1.849, 1.64282, 47.9, 12.799),
        (28.34, 4.625, 1.0, 0.0, 11.512),
        (0.0, 2.554, 1.0, 0.0, 11.655, STOP),
        (0.0, 1.849, 1.58241, 40.6, 13.017),
        (32.19, 7.271, 1.69347, 53.5, 16.0),
        (-52.99, 82.04568, 1.0, 0.0, 16.0),
    )),
    # L. Bertele, US 1,975,678 (1934): Zeiss's Sonnar, f/1.5, scaled to 92.6 mm. Two cemented triplets.
    'sonnar': dict(label='Sonnar (1934)', fnumber=1.5, image_height=35.527, surfaces=(
        (60.61502, 10.5, 1.6375, 56.1, 34.234),
        (416.77, 0.5, 1.0, 0.0, 33.609),
        (37.26, 11.7, 1.6727, 47.3, 26.744),
        (104.34, 7.6, 1.4675, 65.7, 24.807),
        (-247.0, 1.9, 1.689, 31.0, 22.554),
        (22.14, 11.95, 1.0, 0.0, 17.103),
        (0.0, 1.95, 1.0, 0.0, 16.646, STOP),
        (1904.0, 3.4, 1.5481, 45.9, 18.33),
        (59.85, 22.4, 1.6578, 51.2, 21.584),
        (-22.06, 8.4, 1.5488, 63.0, 21.696),
        (-89.06, 34.75113, 1.0, 0.0, 26.698),
    )),
    # R. Richter, US 1,792,917 (1931): Zeiss's Topogon wide angle, f/4.5, 100 mm, 65 degrees across.
    'topogon': dict(label='Topogon (1931)', fnumber=4.5, image_height=63.864, surfaces=(
        (25.9, 5.12, 1.61087, 55.8, 12.0),
        (-96.1, 2.31, 1.54, 47.4, 12.0),
        (18.41, 0.75, 1.0, 0.0, 9.708),
        (23.78, 3.48, 1.561, 61.1, 9.71),
        (35.54, 2.9, 1.0, 0.0, 9.341),
        (0.0, 2.8, 1.0, 0.0, 9.234, STOP),
        (-33.12, 3.96, 1.56, 61.1, 9.137),
        (-22.74, 1.57, 1.0, 0.0, 9.339),
        (-18.14, 1.88, 1.54, 47.4, 9.201),
        (77.38, 5.56, 1.61087, 55.8, 12.0),
        (-25.37, 86.8221, 1.0, 0.0, 12.0),
    )),
    # K. Isono, US 6,744,570 (2004): a four-element phone camera lens, 7.3 mm f/4, with its infrared filter (the flat
    # plate in front of the sensor). Its aspheric surfaces count by their radius at the axis, as paraxial optics does.
    'phone': dict(label='Phone Camera (2004)', fnumber=4.0, image_height=4.198, surfaces=(
        (3.548, 1.161, 1.58913, 61.28, 1.634),
        (16.802, 0.593, 1.0, 0.0, 1.174),
        (0.0, 1.343, 1.0, 0.0, 0.732, STOP),
        (-3.817, 1.377, 1.53048, 55.72, 1.341),
        (-1.576, 0.447, 1.0, 0.0, 1.695),
        (-2.73, 1.686, 1.5834, 30.23, 1.868),
        (-4.28, 0.1, 1.0, 0.0, 2.507),
        (-5.779, 0.833, 1.53048, 55.72, 2.615),
        (5.219, 0.5, 1.0, 0.0, 3.272),
        (0.0, 0.7, 1.5168, 64.2, 3.581),
        (0.0, 0.5437664, 1.0, 0.0, 3.774),
    )),
}
