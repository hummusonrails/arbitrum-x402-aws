#!/usr/bin/env bash
#
# Toggle Ghostty "presentation mode" for the CURRENT window (webinar-friendly:
# bigger font + high contrast). Run it once to turn presentation mode ON, run
# the same command again to restore your terminal exactly as it was.
#
# Why this approach: Ghostty only resizes the *live* window's font through its
# own keybindings (a font-size config change applies to new terminals only), so
# we drive cmd+= / cmd+0 with osascript. The first run will ask macOS for
# permission to control "System Events" (Accessibility / Automation) — grant it
# once and font resizing works thereafter. Colors are changed in-band with OSC
# escape sequences and reset cleanly, so no config files are touched.
#
set -uo pipefail

STATE="${TMPDIR:-/tmp}/x402-present.state"
STEPS=8   # number of font-size increments for presentation mode (tune to taste)

# Controlling terminal, so OSC color codes target THIS window.
TTY="$(tty 2>/dev/null)"
[ -n "$TTY" ] && [ -e "$TTY" ] || TTY=/dev/tty

# Send Cmd+<key> to the frontmost app (Ghostty, since you ran this in it).
# key codes (US layout): 24 = "="  -> cmd+= increases font; 29 = "0" -> cmd+0 resets font.
cmd_key() {
  osascript -e "tell application \"System Events\" to key code $1 using {command down}" \
    >/dev/null 2>&1
}

if [ -f "$STATE" ]; then
  # ---- restore ----
  cmd_key 29                                          # reset font to your config default
  printf '\033]110\a\033]111\a\033]104\a' >"$TTY"     # reset foreground / background / palette
  rm -f "$STATE"
  echo "Presentation mode OFF — terminal restored to your normal settings."
else
  # ---- presentation ----
  cmd_key 29                                          # start from your default size
  for _ in $(seq 1 "$STEPS"); do cmd_key 24; done     # bump the font size up
  printf '\033]11;#0B0F1A\a\033]10;#FFFFFF\a' >"$TTY" # near-black background, white text (high contrast)
  : >"$STATE"
  echo "Presentation mode ON — larger font + high contrast. Run the same command again to restore."
fi
