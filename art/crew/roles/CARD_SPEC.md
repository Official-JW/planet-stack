# Crew role card: template spec (pick screen)

The cards are built by `_src/cards3x.py` from `_src/roles_table.py`. To make a new card, add the role to the table, render its portrait and run the script (see README.md).

## Canvas
| | |
|---|---|
| Size | **1125 × 480 px**, which is **375 × 160 pt @3x**. One full-width row on a 375 pt wide screen, so the 10 roles make a scrolling list |
| Format | 8-bit palette PNG (median cut, up to 255 colours, Floyd–Steinberg dither). Index 255 is fully transparent and is used for the two chamfered corners |
| Budget | **≤ 60 KB** per card. The script steps down 255 → 224 → … colours until the card fits. In the final set every card is well under budget at 255 colours |
| Shape | Rectangle with a 36 px 45° chamfer on the top-left and bottom-right corners. Everything outside it is transparent |

## Layers (back to front, px at 3x)
1. **Background**: vertical gradient from `#1a1f27` (top) to `#0d1015` (bottom).
2. **Portrait window**: x 24–444, y 24–456 (420 × 432), with a 24 px chamfer. Inside it:
   - a `#090b0f` well;
   - a soft accent glow (ellipse, 95/255 alpha, 70 px blur);
   - the portrait, masked to the window;
   - a 3 px accent outline.
3. **Portrait**: `proofs/_raw/portrait/portrait_<role>.png`. This is a Cycles render on a transparent film at 840 × 864 (2×), downsized with Lanczos. The camera is a 3/4 front view from the tool-hand side (`card_az`, default −24°), with a 62 mm lens, target z 1.2 m and the camera 2.75 m away at z 1.42 m. The frame runs from the helmet to mid-thigh and shows the hand tool.
4. **Badge medallion**: 112 px, centred on the portrait window's lower-right corner at (444, 456), with a 4 px blurred dark drop. Drawn by `badge2d.badge_icon`: an accent ring, a `#1d222a` disc and a `#f2f4f7` symbol.
5. **Text column** (x = 486). Rajdhani, SIL OFL.

   | Element | Position | Font | Colour |
   |---|---|---|---|
   | `NN / GROUP` | y 48 | Bold 30 for the number (accent), SemiBold 30 for the group label | `#8a94a0` |
   | Role name, upper case | y 92 | Bold 100, auto-shrinks to fit 583 px | `#f4f6f9` |
   | Accent rule | x 486–606, y 214–220 | | accent |
   | Job line | y 240, wraps at 583 px, 2 lines max | Medium 46 | `#c4cdd8` |
   | `KIT` + tool label | y 392 | Bold 28 for KIT (accent), SemiBold 28 for the label | `#8a94a0` |

   The group label is STARTING CREW, FLIGHT CREW or SPECIALIST.
6. **Frame**: a 6 px accent outline inset 3 px, following the chamfer. Two accent corner ticks (6 px wide, 70 px legs) sit in the top-right and bottom-left corners.

## Colour rules
- The accent comes only from `roles_table.ROLES[k]['accent']`, which is also `roles.json → accent`. The same hex is used for the suit paint, the badge ring, the card frame and the glow.
- Suit colours shared by every role stay fixed: shell `#eceef1`, graphite `#2b3038`, gold visor `#ffae2e`, cyan glow `#3ad0ff`. Accents are checked against the cyan glow and the visor too.
- `_src/palette_check.py` gives the minimum pairwise CIEDE2000 for the current palette:

  | Vision | Min ΔE00 |
  |---|---|
  | Normal | 17.8 |
  | Protan | 14.2 |
  | Deutan | 13.1 |
  | Tritan | 9.1 |

  The simulations are Machado 2009 at severity 1.0. For every role pair under every simulation, the badge shape is a second cue (`proofs/palette_cvd.png`).
- Badges are original, simple geometric icons with no text and no logos. Do not use diamond, rhombus, crystal, gem or 4-point-star shapes, because crystals are the paid currency.

## States (for the UI to apply; not baked into the PNG)
- **Selected**: scale 1.0, with a +2 pt accent outer glow drawn by the UI.
- **Available**: as baked.
- **Locked** (for example, Captain or Co-Captain before the Habitat): the UI overlays 55 % `#0d1015` and a lock glyph. The baked card stays the same.
