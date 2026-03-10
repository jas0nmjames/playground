import './style.css'
import { startGame } from './scravax/game'

startGame().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err)
  const el = document.getElementById('netStatus')
  if (el) el.textContent = 'Error'
})
