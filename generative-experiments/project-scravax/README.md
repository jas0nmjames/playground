# Scravax Drift Derby (Georgia)

A kid-friendly 3D racing prototype (ages 6+) inspired by arcade street racing and off-road vibes:

- Steer + drift
- “Minecraft-like” on-screen **levers** (touch controls) plus keyboard controls
- **+5 points** for each second you drive **over 100 mph**
- Race objective: **pass all other cars** and be **1st at the finish line**
- Multiplayer (prototype): **peer-to-peer** sync so your friend’s car appears on your screen

## Run it

```bash
npm install
npm run dev
```

Open the printed local URL on your Mac, iPad, or another device on the same network.

## Controls

- **Keyboard**: `W` accelerate, `S` brake, `A/D` steer, `Space` or `Shift` drift
- **Touch**:
  - Left lever: steer
  - Right lever: gas (up) / brake (down)
  - Tap **Drift** to toggle drift mode

## Multiplayer (2 devices)

1. On device A: click **Multiplayer** → **Create offer** → copy the offer text.
2. On device B: paste offer into **Join** → **Create answer** → copy the answer text.
3. Back on device A: paste the answer into **Set answer**.

When connected, each player will see the other player’s car.

> Note: This uses WebRTC for transport. “Bluetooth pairing” isn’t implemented in this web prototype; you can still *share the handshake text* via Messages/AirDrop (which may use Bluetooth under the hood).

