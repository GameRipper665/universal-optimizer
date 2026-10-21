# Cloud gaming

**Scope.** GeForce NOW, Xbox Cloud Gaming, PlayStation Plus cloud streaming, Boosteroid, Amazon Luna. The game
runs on the provider's server. **Nothing the user does changes the remote game's own frame rate, settings files or
engine.** What the user controls is the stream: bandwidth, latency, jitter, packet loss, the client's decoder and
the display. `uo bench`/PresentMon measure only the local client, not the remote game; use each service's stats
overlay instead. No local game files exist to patch, so Tier 2/3 of the main loop do not apply.

**Where the time usually goes.**
- **Network latency and jitter.** Input -> server -> encoded video -> client. Latency over budget feels like input
  lag; jitter and loss feel like stutter and blocky video.
- **Bitrate starvation.** Compression artefacts in motion, from a congested link or a low bitrate setting.
- **Client decode.** Weak or software video decode adds delay and drops frames.
- **Display path.** TV post-processing, V-sync/VRR mismatch, wrong refresh rate.
- **Server load or distance.** Region and queue; the user can only influence this by where they are and what the
  service offers.

## Tier 1: the network and the client

**Connection.**
- NVIDIA recommends wired Ethernet or a router on 5 GHz Wi-Fi, and under 80 ms latency to its data center
  ([GeForce NOW requirements](https://www.nvidia.com/en-us/geforce-now/system-reqs/)). 6 GHz Wi-Fi (Wi-Fi 6E/7)
  follows the same logic (less interference); no service page found that states it (unverified as vendor advice).
- Wi-Fi tips that are real: sit in the same room as the router, use a 5/6 GHz SSID only for the streaming device,
  pick a clear channel, avoid mesh backhaul hops. Not real: "gaming" Wi-Fi extenders that add a hop.
- **Router QoS / SQM.** Smart queue management (fq_codel/CAKE) on the router reduces latency spikes when someone
  else saturates the link; it needs a router that supports it and a correctly set upload/download shaper (about
  90-95% of measured speed). Generic "game mode" priority lists are vendor-specific and unmeasured; test with the
  stream stats before and after.
- Stop other uploads/downloads and cloud backups on the network while playing.

**Per-service stream settings.**

| Service | What is documented | Source |
|---|---|---|
| GeForce NOW | 25 Mbps for 1080p60, 15 for 720p60, 35 for QHD/120, 45 for 4K/120, 55 for 1080p 240-360, 65 for 5K/120; browser tops out at 1080p60 (QHD/120 needs the top tier, Firefox on Windows can reach 1440p120 since 2.0.88); 4K/5K and 240+ fps are native-app features | [requirements](https://www.nvidia.com/en-us/geforce-now/system-reqs/), [release highlights](https://www.nvidia.com/en-us/geforce-now/release-highlights/) |
| Xbox Cloud Gaming | 1440p streaming on Xbox consoles needs Game Pass Ultimate for supported games; about 9 GB/h at 1080p vs up to 14 GB/h at 1440p | [Thurrott, Feb 2026](https://www.thurrott.com/games/333068/xbox-cloud-gaming-now-supports-1440p-streaming-on-xbox-consoles) |
| PlayStation Plus cloud streaming | Premium tier; streaming PS5 games to a PlayStation Portal; session setup 5 Mbps, 720p 7 Mbps, 1080p 13 Mbps (another line on the page says 15 Mbps; plan for 15); Wi-Fi/broadband required; PS5 titles only | [PlayStation](https://www.playstation.com/en-us/ps-plus-portal-cloud-streaming/) |
| Boosteroid | Resolution selector in Settings > Advanced Settings, Windows app only (as of a 2026 post); older figures ~15 Mbps for 1080p60, ~13 Mbps on Android; match your display's native resolution | [Boosteroid blog](https://boosteroid.com/blog/?p=8932), third-party for bandwidth (unverified for current numbers) |
| Amazon Luna | Still running but restructured in 2026: store and third-party channels removed, folded into Prime Video on Fire TV (US/UK) per secondary reports. Treat availability as (unverified) and check Amazon | [PC Gamer](https://www.pcgamer.com/software/platforms/amazons-luna-cloud-gaming-service-is-ending-support-for-game-purchases-and-subscriptions-from-third-party-stores-and-users-will-lose-streaming-access-to-purchased-third-party-games-in-june/), [Wikipedia](https://en.wikipedia.org/wiki/Amazon_Luna) |

Xbox Cloud Gaming network minimums (about 20 Mbps console, 30+ recommended) come from a third-party guide only
(unverified); Microsoft's own page was not retrievable. Xbox's in-session stats display and quality-picker path:
(unverified).

**GeForce NOW levers (documented in the client release notes).**
- Streaming statistics overlay: Ctrl+N (Windows/ChromeOS/browser) or Cmd+N (macOS); the same key toggles Standard
  and Compact; it shows the active codec (H.264, H.265 or AV1) ([release highlights](https://www.nvidia.com/en-us/geforce-now/release-highlights/)).
- "Adjust for network conditions": Optimal Latency vs Optimal Quality. In Custom quality mode you can change
  bitrate, V-sync and upscaling live from the overlay (Ctrl+G > Settings > Gameplay). Settings > Gameplay > Custom >
  Codec lets you override the automatic codec to troubleshoot corruption or performance (same source). Trade-off:
  higher bitrate means more bandwidth and more sensitivity to loss; lower bitrate means artefacts.
- "Color precision" 10-bit is recommended by NVIDIA (same source). Needs a display path that handles it.
- Game Session Diagnostic analyzes the last session and suggests fixes; limited to some members on the Windows and
  macOS apps (same source).
- **Server region:** the release notes show no manual server picker; login picks a provider by location
  (same source). A cloud service's own status page shows rollout, not a way to move you.

**Codecs and decode.**
- Use the native app over the browser when the service offers one; NVIDIA reserves 4K/5K and 240+ fps for native
  apps and caps browsers (see table).
- Hardware decode on the client matters most for latency. AV1 needs an AV1-capable decoder: NVIDIA says RTX 30
  series GPUs have a dedicated AV1 hardware decoder ([NVIDIA](https://nvidia.com/en-us/geforce/news/rtx-30-series-av1-decoding));
  GeForce NOW added AV1 on Macs with M3-class GPUs ([release highlights](https://www.nvidia.com/en-us/geforce-now/release-highlights/)).
  GeForce NOW's exact AV1 server and client requirements are unconfirmed here (unverified; a forum claim says the
  server needs a 40-series and the client a 30-series).
- In a browser: enable hardware acceleration in Edge/Chrome settings and disable extensions during sessions
  (guide advice, [Digital Citizen](https://www.digitalcitizen.life/how-to-optimise-your-network-for-xbox-cloud-gaming-step-by-step/), secondary).
- AV1 usually uses less bandwidth at similar quality; HEVC can retain 4:4:4 chroma in some cases (forum claim,
  unverified). If a codec shows corruption, switch codecs rather than lowering resolution.

**Display.** Match the stream rate to the display rate (60 fps on a 60 Hz output; 120 on a 120 Hz output). A TV
should be in Game Mode/ALLM to cut its own processing delay (see consoles.md). VRR only helps if the stream is
variable; GeForce NOW's Windows/macOS clients make 120 fps streams follow the game's frame rate when it drops
below 120 (release highlights).

## Measuring (stream, not game)
- Read the overlay's round-trip latency, bitrate, resolution, frame rate, packet loss and codec, in the same game
  scene, at the same time of day. Peak-hour congestion is the biggest uncontrolled variable.
- Keep a log of one number per change (wired vs Wi-Fi, SQM on vs off, codec A vs B). Same rule as the main loop:
  change one thing, measure twice, revert what does not beat noise.
- Latency compared to a local console/PC cannot reach zero; a stream adds encode, transport and decode time.
  Latency-critical genres (fighters, rhythm, competitive shooters) are better local.

## Gotchas
- **"Increase bitrate to the max"** -> on a congested link causes packet loss, which looks worse than a lower rate.
- **Wi-Fi power saving on the client** -> latency spikes. Disable it on the adapter (`Power Management` tab on
  Windows).
- **VPNs** -> add distance; turn off while streaming unless required.
- **Region mismatch** -> a service picks the server by your location; travelling or a VPN changes it.
- **Blocky dark scenes** -> bitrate allocation, not the game. Try 10-bit colour and a different codec.
- **Mobile data** -> streams use roughly 9-14 GB/h at high quality on Xbox (Thurrott above).

## Out of scope
- Anything that bypasses the service's terms (spoofed regions, modified clients). No local game files or
  anti-cheat touch points exist here; the remote host is the provider's.
- Overclocking the router or modifying firmware for "speed"; update official firmware and use QoS/SQM instead.
