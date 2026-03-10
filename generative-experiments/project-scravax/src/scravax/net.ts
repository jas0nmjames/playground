import { nanoid } from 'nanoid'

export type NetPeerState = {
  id: string
  name: string
  color: number
  x: number
  y: number
  z: number
  vx: number
  vz: number
  yaw: number
  progress: number
  lap: number
  finished: boolean
  t: number
}

type Msg =
  | { type: 'hello'; id: string; name: string; color: number }
  | { type: 'state'; s: NetPeerState }

function encode(msg: Msg) {
  return JSON.stringify(msg)
}
function decode(raw: string): Msg | null {
  try {
    return JSON.parse(raw) as Msg
  } catch {
    return null
  }
}

export type NetSession = {
  localId: string
  localName: string
  localColor: number
  connectionLabel: () => string
  isConnected: () => boolean
  createOffer: () => Promise<string>
  acceptOfferCreateAnswer: (offer: string) => Promise<string>
  acceptAnswer: (answer: string) => Promise<void>
  sendState: (s: Omit<NetPeerState, 'id' | 'name' | 'color'>) => void
  onPeerHello: (cb: (p: { id: string; name: string; color: number }) => void) => void
  onPeerState: (cb: (s: NetPeerState) => void) => void
  close: () => void
}

export function createNetSession(): NetSession {
  const localId = nanoid(10)
  const localName = `Driver-${localId.slice(0, 4)}`
  const localColor = 0x55aaff

  let pc: RTCPeerConnection | null = null
  let dc: RTCDataChannel | null = null
  let peerHelloCb: ((p: { id: string; name: string; color: number }) => void) | null = null
  let peerStateCb: ((s: NetPeerState) => void) | null = null

  const ensure = () => {
    if (pc) return
    pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    })
    pc.ondatachannel = (e) => {
      dc = e.channel
      wireDc()
    }
  }

  const wireDc = () => {
    if (!dc) return
    dc.onmessage = (e) => {
      const msg = decode(String(e.data))
      if (!msg) return
      if (msg.type === 'hello') peerHelloCb?.(msg)
      if (msg.type === 'state') peerStateCb?.(msg.s)
    }
    dc.onopen = () => {
      dc?.send(encode({ type: 'hello', id: localId, name: localName, color: localColor }))
    }
  }

  const gather = async () => {
    if (!pc) throw new Error('peer connection not created')
    const localPc = pc
    if (localPc.iceGatheringState === 'complete') return
    await new Promise<void>((resolve) => {
      const onChange = () => {
        if (localPc.iceGatheringState === 'complete') {
          localPc.removeEventListener('icegatheringstatechange', onChange)
          resolve()
        }
      }
      localPc.addEventListener('icegatheringstatechange', onChange)
      onChange()
      setTimeout(resolve, 2000) // best-effort fallback
    })
  }

  const createOffer = async () => {
    ensure()
    if (!pc) throw new Error('pc missing')
    dc = pc.createDataChannel('scravax')
    wireDc()
    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await gather()
    return JSON.stringify(pc.localDescription)
  }

  const acceptOfferCreateAnswer = async (offer: string) => {
    ensure()
    if (!pc) throw new Error('pc missing')
    const desc = JSON.parse(offer) as RTCSessionDescriptionInit
    await pc.setRemoteDescription(desc)
    const answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await gather()
    return JSON.stringify(pc.localDescription)
  }

  const acceptAnswer = async (answer: string) => {
    if (!pc) throw new Error('Create an offer first')
    const desc = JSON.parse(answer) as RTCSessionDescriptionInit
    await pc.setRemoteDescription(desc)
  }

  const sendState = (s: Omit<NetPeerState, 'id' | 'name' | 'color'>) => {
    if (!dc || dc.readyState !== 'open') return
    const msg: Msg = {
      type: 'state',
      s: { ...s, id: localId, name: localName, color: localColor },
    }
    dc.send(encode(msg))
  }

  const close = () => {
    try {
      dc?.close()
    } catch {
      // ignore
    }
    try {
      pc?.close()
    } catch {
      // ignore
    }
    dc = null
    pc = null
  }

  return {
    localId,
    localName,
    localColor,
    connectionLabel: () => (dc?.readyState === 'open' ? 'Connected' : pc ? 'Connecting' : 'Solo'),
    isConnected: () => dc?.readyState === 'open',
    createOffer,
    acceptOfferCreateAnswer,
    acceptAnswer,
    sendState,
    onPeerHello: (cb) => (peerHelloCb = cb),
    onPeerState: (cb) => (peerStateCb = cb),
    close,
  }
}

