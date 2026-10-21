# Consoles (PlayStation, Xbox, Nintendo Switch / Switch 2)

**Scope.** Consoles run a fixed hardware target, so the player has far fewer levers than on PC, and `uo bench`
does not apply (no PresentMon on a console). What a player can do is pick the right mode, set the display chain
correctly, and manage storage. Nothing changes the game's own code or its frame budget.

**Steam Deck is a PC.** Do not treat it as a console: use `universal-layers.md`, section "Linux / Steam Deck,
briefly" (MangoHud, gamescope, Proton), and the engine playbooks.

**Where the time usually goes.**
- **The game's own mode choice.** A game targeting 4K at 30 fps is GPU-bound by design; a performance mode drops
  resolution or effects to hit 60 or 120.
- **The display chain.** A TV with image processing adds input lag; a missing HDMI 2.1 feature stops 120 Hz/VRR.
- **Storage.** Load times depend on where the game is installed.
- **Network** for online games (latency, NAT type, Wi-Fi quality).

## Tier 1: what a player can do (all official, no modification)

### Graphics modes
- Most current games ship a Performance mode (higher frame rate, lower resolution/effects) and a
  Quality/Fidelity/Resolution mode (higher resolution, ray tracing, 30-40 fps). This is the largest lever and is
  per game, in the game's own menu. Trade-off: visuals vs smoothness; 120 Hz modes need a 120 Hz-capable display.
- PS5 has a system-level preset (Settings > Saved Data and Game/App Settings > Game Presets) per a third-party
  guide ([source](https://portkeygamessupport.wbgames.com/hc/en-us/articles/13653581968659-Adjusting-Performance-or-Fidelity-Mode-On-PlayStation-5));
  the path was not confirmed on a Sony page (unverified). The game's own setting usually overrides it.

### Display chain (TV and cables)
- **TV "Game Mode"/ALLM.** Turns off most image processing to cut input lag. Consoles send an ALLM signal on
  supported TVs; the manual TV setting is the fallback. See the PS5 note: setting ALLM to Off does not stop the TV
  switching to its low-latency mode while VRR is active ([PlayStation video output guide](https://www.playstation.com/en-us/support/hardware/ps5-4k-resolution-guide/)).
- **PS5:** Settings > Screen and Video > Video Output. "120 Hz Output" allows 120 Hz on compatible TVs/games; turn
  it off if the display shows video problems. VRR and ALLM are in the same menu area (same PlayStation guide). A
  third-party wiki recommends VRR "Automatic" (community advice, unverified).
- **Xbox Series X|S:** Settings > General > TV & display options > Video modes: enable only what your display
  supports (4K, HDR10, Allow variable refresh rate, Allow auto low-latency mode), and set Refresh rate separately
  ([guides](https://www.digitaltrends.com/gaming/xbox-series-x-settings-to-change/), secondary; Microsoft page not
  retrievable, unverified). A 120 Hz output does not make a game run at 120 fps; the game needs a high-frame-rate
  mode. 4K at 120 Hz needs HDMI 2.1 on both the TV input and the cable.
- **Switch 2:** Display settings offer TV resolution Automatic/720p/1080p/1440p/2160p and a "120 Hz Output"
  toggle that works only at 1080p and 1440p; VRR output applies in TV mode only; HDR output can be set for all
  software, compatible software only or off. Resolution is only selectable while docked
  ([Nintendo Support](https://en-americas-support.nintendo.com/app/answers/detail/a_id/68188)). Trade-off: 4K
  caps at 60 Hz per that page.
- Use a certified high-speed/ultra-high-speed HDMI cable. Flicker at 4K120 is often the cable or port.

### Console-specific features
- **PS5 Pro.** PSSR (PlayStation Spectral Super Resolution) is the console's AI upscaler; some games let you
  toggle it (e.g. [Alan Wake 2](https://www.techradar.com/gaming/alan-wake-2-now-lets-you-turn-off-pssr-on-ps5-pro)).
  A 2026 system update added an upgraded PSSR with a toggle in Screen and Video settings that can be forced on
  supported titles, with possible artefacts (secondary reports:
  [TechRadar](https://www.techradar.com/gaming/sonys-updated-pssr-upscaling-tech-is-finally-available-for-even-more-ps5-pro-games-including-crimson-desert-silent-hill-f-dragon-age-the-veilguard-and-more),
  [Engadget](https://engadget.com/gaming/playstation/sonys-enhanced-pssr-upscaling-arrives-on-ps5-pro-today-201020423.html);
  menu wording unverified). "PS5 Pro Game Boost" is reported to make PS4/PS5 games run more stable or at a higher
  frame rate automatically; the game list and exact behaviour are not confirmed here (unverified). Trade-off:
  per-game results vary and are not user-configurable beyond the toggles.
- **Xbox FPS Boost and Auto HDR.** Optional system-level features for selected backward-compatible games on
  Series X|S: FPS Boost raises the frame rate (often doubling a 30 fps game) without developer changes; Auto HDR adds
  HDR to older SDR games. Both are toggled per game under Manage > Compatibility options
  ([Xbox Wire](https://news.xbox.com/en-us/fpsboost/), [CGMagazine](https://www.cgmagonline.com/news/xbox-backwards-compatible-team-introduces-new-xbox-series-x-s-feature-fps-boost)).
  Trade-off: FPS Boost can expose bugs in games tied to frame rate; turn it off if the game misbehaves. The
  supported-title list changes; check the [backward compatibility page](https://www.xbox.com/en-us/games/backward-compatibility).
- **Switch 2.** Docked: up to 4K at 60 fps, or 120 fps at 1080p/1440p; handheld: 1080p with VRR up to 120 Hz, per
  Nintendo's published specs as reported by [Nintendo Life](https://www.nintendolife.com/guides/nintendo-switch-2-specs-how-powerful-is-the-new-switch)
  and [mein-mmo](https://mein-mmo.de/en/nintendo-switch-2-here-are-the-official-specifications,1245779/)
  (secondary). Games typically run at lower settings handheld to save battery (secondary:
  [Techbook](https://www.techbook.de/home-entertainment/gaming-konsolen/switch-2-leistung)). Per-game results vary.

### Storage
- **PS5 internal NVMe expansion.** Needs a PCIe Gen4 x4 NVMe M.2 drive with an M key; SATA M.2 is unsupported;
  250 GB to 8 TB; 5,500 MB/s or faster recommended; must be cooled (heatsink within 11.25 mm total thickness);
  sizes 2230/2242/2260/2280/22110. Even with a fast drive, some games may not perform as on the internal SSD
  ([PlayStation guide](https://www.playstation.com/en-us/support/hardware/ps5-install-m2-ssd/)).
- **PS5 external USB.** For PS4 games and for storing PS5 games, not for playing PS5 games (PlayStation's guidance;
  not fetched here, unverified).
- **Xbox Series X|S.** Current-generation games need the internal SSD or an official Storage Expansion Card to run;
  a USB drive can store them but not run them, though it can run backward-compatible titles (several secondary
  sources, e.g. [BGR](https://www.bgr.com/2285557/things-users-wish-they-knew-before-buying-xbox-series-x/);
  Microsoft page not retrieved, unverified). Quick Resume snapshots use internal or expansion-card space, so a
  small drive limits how many games it can hold.
- Keep ~10-15% of the drive free for updates (rule of thumb, unverified).

### Rest mode, Quick Resume, power
- **Rest mode and Quick Resume** save time but keep the console on. After a system or game update, or after weeks
  of uptime, a full restart clears any odd state (user reports, not documented: stutter that appears after days of rest mode).
- PS5 downloads during rest mode only if "Stay Connected to the Internet" is on, found under Settings > System >
  Power Saving > Features Available in Rest Mode ([PlayStation](https://www.playstation.com/en-bg/support/hardware/automatic-updates-playstation/)).
- Stay on the latest system and game updates; they ship performance patches.
- Ventilation: leave space around the console; dust and enclosed cabinets cause thermal throttling and fan noise.
  Cleaning the vents is safe; opening the console voids warranty.

### Network (online play)
- Wired Ethernet beats Wi-Fi for latency and jitter. If Wi-Fi is the only option, use a 5 GHz connection close to
  the router.
- Open or moderate NAT matters for peer-to-peer matchmaking; use UPnP rather than DMZ or full port exposure.
- SQM/QoS on the router (fq_codel/CAKE) helps when others use the link (see cloud.md for the same advice).
- Cloud streaming on consoles: see `cloud.md`.

## Tier 2: not available
No drop-in layers, config files or wrappers exist on stock consoles. Do not suggest mods.

## Tier 3: developer side (licensed developers only)
Console profilers ship with platform SDKs under NDA and need licensed access. The agent should only use them if the
user confirms they are a licensed developer with SDK access; it should not try to obtain, guess or reproduce them.
- **Xbox:** PIX on Xbox (GDK) for GPU captures, timing captures and GPU traces; installed with the GDK
  ([Xbox docs](https://devdocs.xbox.com/tools/tools-console/pix)). PIX for Windows is the PC-only counterpart.
- **PlayStation:** Razor (CPU/GPU profilers) is named in Sony job listings as the GPU performance tool, but its
  documentation is on the PlayStation Partners portal and not public (name confirmed only by job postings;
  treat as unverified).
- **Nintendo:** the Nintendo Developer Portal; tool names (unverified).

## Gotchas
- **"120 Hz on" but the game stays at 60** -> the game has no 120 fps mode, or the resolution/HDMI mode does not
  allow it; check the game's mode menu and the output info screen.
- **Blurry image after enabling Performance mode** -> expected; the game lowered resolution. Pick the mode that
  fits what you want.
- **Input lag on a new TV** -> Game Mode off; turn it on or use ALLM.
- **Sudden stutter after months of rest mode** (anecdotal) -> restart; also check free space and updates.
- **FPS Boost game behaves oddly** -> disable the compatibility option for that game.

## Out of scope
- **Jailbreaking, custom firmware, homebrew loaders, modded BIOS or "FPS unlockers".** They risk online bans and
  bricking, and involve defeating DRM or signature checks, which this toolkit does not do or help with.
- **Emulating consoles on PC** (owned games, owned hardware): covered in `engines/emulators.md`.
