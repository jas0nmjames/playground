import { Game } from './Game.js';

const root = document.getElementById('game');
const game = new Game(root);

// Expose for debugging:
window.__game = game;
